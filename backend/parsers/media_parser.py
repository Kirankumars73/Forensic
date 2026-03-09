"""
Media Parser: Extracts EXIF metadata, GPS coords, and generates thumbnails.
"""
import os
import json
import hashlib
import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".3gp", ".wmv", ".flv", ".m4v"}
AUDIO_EXTS = {".mp3", ".aac", ".ogg", ".wav", ".flac", ".m4a", ".opus", ".amr"}


def _sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk_data in iter(lambda: f.read(chunk), b""):
                h.update(chunk_data)
        return h.hexdigest()
    except Exception:
        return ""


def _gps_to_decimal(gps_tuple, ref):
    """Convert EXIF GPS tuple to decimal degrees."""
    try:
        d = float(gps_tuple[0])
        m = float(gps_tuple[1])
        s = float(gps_tuple[2])
        dec = d + m / 60 + s / 3600
        if ref in ("S", "W"):
            dec = -dec
        return round(dec, 7)
    except Exception:
        return None


def parse_media_file(file_path, thumbnail_dir=None, device_id=None):
    """
    Parse a single media file and return a dict with metadata.
    Generates thumbnail if it's an image.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        file_type = "photo"
    elif ext in VIDEO_EXTS:
        file_type = "video"
    elif ext in AUDIO_EXTS:
        file_type = "audio"
    else:
        file_type = "document"

    stat = path.stat()
    file_size = stat.st_size
    file_hash = _sha256(file_path)
    mod_time = datetime.datetime.utcfromtimestamp(stat.st_mtime)

    result = {
        "filename": path.name,
        "file_type": file_type,
        "file_size": file_size,
        "file_hash": file_hash,
        "local_path": str(file_path),
        "thumbnail_path": None,
        "timestamp": mod_time,
        "camera_make": None,
        "camera_model": None,
        "gps_latitude": None,
        "gps_longitude": None,
        "gps_altitude": None,
        "width": None,
        "height": None,
        "source_path": str(file_path),
    }

    if file_type == "photo":
        try:
            from PIL import Image as PILImage, ExifTags, TiffImagePlugin
            with PILImage.open(file_path) as img:
                result["width"] = img.width
                result["height"] = img.height

                # Get EXIF data
                exif_data = {}
                try:
                    raw_exif = img._getexif()
                    if raw_exif:
                        for tag_id, value in raw_exif.items():
                            tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode("utf-8", errors="replace")
                                except Exception:
                                    value = str(value)
                            exif_data[tag] = value
                except Exception:
                    pass

                result["camera_make"] = exif_data.get("Make", "")
                result["camera_model"] = exif_data.get("Model", "")

                # DateTimeOriginal
                dt_str = exif_data.get("DateTimeOriginal", exif_data.get("DateTime", ""))
                if dt_str:
                    try:
                        result["timestamp"] = datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    except Exception:
                        pass

                # GPS
                gps_info = exif_data.get("GPSInfo", {})
                if gps_info:
                    try:
                        from PIL.ExifTags import GPSTAGS
                        gps = {}
                        for k, v in gps_info.items():
                            gps[GPSTAGS.get(k, k)] = v

                        lat_ref = gps.get("GPSLatitudeRef", "N")
                        lon_ref = gps.get("GPSLongitudeRef", "E")
                        lat_t = gps.get("GPSLatitude")
                        lon_t = gps.get("GPSLongitude")
                        alt_t = gps.get("GPSAltitude")

                        if lat_t and lon_t:
                            result["gps_latitude"] = _gps_to_decimal(
                                [float(x) if not hasattr(x, 'numerator') else x.numerator / x.denominator for x in lat_t], lat_ref
                            )
                            result["gps_longitude"] = _gps_to_decimal(
                                [float(x) if not hasattr(x, 'numerator') else x.numerator / x.denominator for x in lon_t], lon_ref
                            )
                        if alt_t:
                            try:
                                result["gps_altitude"] = float(alt_t)
                            except Exception:
                                pass
                    except Exception as e:
                        logger.debug("GPS parse error: %s", e)

                # Generate thumbnail
                if thumbnail_dir:
                    os.makedirs(thumbnail_dir, exist_ok=True)
                    thumb_name = f"{file_hash[:16]}_{path.stem}.jpg"
                    thumb_path = os.path.join(thumbnail_dir, thumb_name)
                    if not os.path.exists(thumb_path):
                        try:
                            img_copy = img.copy()
                            img_copy.thumbnail((320, 320), PILImage.LANCZOS)
                            img_copy = img_copy.convert("RGB")
                            img_copy.save(thumb_path, "JPEG", quality=75)
                        except Exception as e:
                            logger.debug("Thumbnail error: %s", e)
                    result["thumbnail_path"] = thumb_path

        except ImportError:
            logger.warning("Pillow not installed, skipping EXIF extraction")
        except Exception as e:
            logger.debug("Image parse error for %s: %s", file_path, e)

    return result


def parse_media_directory(directory, thumbnail_dir=None, device_id=None):
    """Parse all media files in a directory recursively."""
    results = []
    for root, _, files in os.walk(directory):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = Path(fname).suffix.lower()
            if ext in IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS:
                meta = parse_media_file(fpath, thumbnail_dir=thumbnail_dir, device_id=device_id)
                if meta:
                    results.append(meta)
    return results
