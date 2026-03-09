"""
PDF Report Generator using ReportLab.
Generates a professional forensic evidence report.
"""
import os
import datetime
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas

# Color palette
DARK_BLUE = colors.HexColor("#0a1628")
ACCENT_BLUE = colors.HexColor("#1e3a5f")
CYAN = colors.HexColor("#00bcd4")
LIGHT_GRAY = colors.HexColor("#f0f4f8")
MID_GRAY = colors.HexColor("#b0b8c4")
WHITE = colors.white
RED = colors.HexColor("#e53935")
GREEN = colors.HexColor("#43a047")
ORANGE = colors.HexColor("#fb8c00")


def _header_footer(canvas_obj, doc):
    """Draw header and footer on every page."""
    canvas_obj.saveState()
    w, h = A4
    # Header bar
    canvas_obj.setFillColor(DARK_BLUE)
    canvas_obj.rect(0, h - 1.5 * cm, w, 1.5 * cm, fill=1, stroke=0)
    canvas_obj.setFillColor(CYAN)
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawString(1.5 * cm, h - 1 * cm, "🔍 MOBILE FORENSICS REPORT — CONFIDENTIAL")
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawRightString(w - 1.5 * cm, h - 1 * cm, f"Page {doc.page}")
    # Footer
    canvas_obj.setFillColor(ACCENT_BLUE)
    canvas_obj.rect(0, 0, w, 0.8 * cm, fill=1, stroke=0)
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(1.5 * cm, 0.25 * cm, f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | FOR OFFICIAL USE ONLY")
    canvas_obj.restoreState()


def generate_report(output_path, case_data, device_data, call_logs, sms_messages,
                    contacts, media_files, app_data, emails, audit_logs,
                    timeline_events=None, thumbnail_dir=None):
    """
    Generate a full forensic PDF report.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=2 * cm, bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("title", fontSize=22, fontName="Helvetica-Bold",
                                  textColor=DARK_BLUE, spaceAfter=6, alignment=TA_CENTER)
    h1 = ParagraphStyle("h1", fontSize=14, fontName="Helvetica-Bold",
                         textColor=DARK_BLUE, spaceBefore=12, spaceAfter=4,
                         borderPad=4, backColor=LIGHT_GRAY)
    h2 = ParagraphStyle("h2", fontSize=11, fontName="Helvetica-Bold",
                         textColor=ACCENT_BLUE, spaceBefore=8, spaceAfter=3)
    normal = ParagraphStyle("norm", fontSize=8, fontName="Helvetica",
                             textColor=colors.black, spaceAfter=2)
    label = ParagraphStyle("lbl", fontSize=8, fontName="Helvetica-Bold",
                            textColor=ACCENT_BLUE)
    monospace = ParagraphStyle("mono", fontSize=7, fontName="Courier",
                                textColor=colors.HexColor("#333333"), spaceAfter=1)
    small = ParagraphStyle("small", fontSize=7, fontName="Helvetica",
                            textColor=MID_GRAY)
    center = ParagraphStyle("center", fontSize=9, fontName="Helvetica",
                             alignment=TA_CENTER, textColor=MID_GRAY)

    story = []

    # ---- COVER PAGE ----
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("MOBILE DEVICE FORENSIC REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=CYAN))
    story.append(Spacer(1, 0.5 * cm))

    case_meta = [
        ["Case Number", case_data.get("case_number", "N/A")],
        ["Case Title", case_data.get("title", "N/A")],
        ["Investigator", case_data.get("investigator", "N/A")],
        ["Agency / Department", case_data.get("agency", "N/A")],
        ["Suspect", case_data.get("suspect_name", "N/A")],
        ["Report Date", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Status", case_data.get("status", "open").upper()],
    ]
    t = Table(case_meta, colWidths=[5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), ACCENT_BLUE),
        ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 1 * cm))

    # Device metadata
    story.append(Paragraph("● DEVICE UNDER EXAMINATION", h2))
    dev_meta = [
        ["Manufacturer", device_data.get("manufacturer", "N/A")],
        ["Model", device_data.get("model", "N/A")],
        ["Android Version", device_data.get("android_version", "N/A")],
        ["IMEI", device_data.get("imei", "N/A")],
        ["Serial Number", device_data.get("serial", "N/A")],
        ["Phone Number", device_data.get("phone_number", "N/A")],
        ["SIM Operator", device_data.get("sim_operator", "N/A")],
        ["Storage", f"{device_data.get('storage_total', 'N/A')} total / {device_data.get('storage_used', 'N/A')} used"],
        ["Battery at Acquisition", device_data.get("battery_level", "N/A")],
        ["Root Access", "YES" if device_data.get("is_rooted") else "NO"],
        ["Acquisition Method", device_data.get("acquisition_type", "logical")],
        ["Acquired At", str(device_data.get("acquired_at", "N/A"))],
    ]
    dt = Table(dev_meta, colWidths=[5 * cm, 11 * cm])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), ACCENT_BLUE),
        ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(dt)
    story.append(PageBreak())

    # ---- SECTION 1: EVIDENCE SUMMARY ----
    story.append(Paragraph("1. EVIDENCE SUMMARY", h1))
    story.append(Spacer(1, 0.3 * cm))
    summary_data = [
        ["Evidence Type", "Count", "Notes"],
        ["Call Logs", str(len(call_logs)), f"Incoming/Outgoing/Missed"],
        ["SMS Messages", str(len(sms_messages)), "Including MMS"],
        ["Contacts", str(len(contacts)), "Device address book"],
        ["Media Files", str(len(media_files)), "Photos, Videos, Audio"],
        ["App Data Records", str(len(app_data)), "WhatsApp, Browser, etc."],
        ["Emails", str(len(emails)), "Gmail and other accounts"],
        ["Timeline Events", str(len(timeline_events or [])), "Unified chronological feed"],
    ]
    st = Table(summary_data, colWidths=[6 * cm, 3 * cm, 7 * cm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.5 * cm))

    # ---- SECTION 2: CALL LOGS ----
    story.append(Paragraph("2. CALL LOGS", h1))
    if call_logs:
        call_table_data = [["#", "Number / Name", "Type", "Duration", "Date / Time", "Location"]]
        for i, c in enumerate(call_logs[:100], 1):  # show up to 100
            call_type = (c.get("call_type") or "").upper()
            ts = c.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts or "")
            dur = c.get("duration_formatted") or c.get("duration_seconds", 0)
            color = GREEN if call_type == "INCOMING" else (ORANGE if call_type == "OUTGOING" else RED)
            call_table_data.append([
                str(i),
                f"{c.get('number','')}\n{c.get('name','')}",
                call_type,
                str(dur),
                ts_str,
                (c.get("geocoded_location") or "")[:30],
            ])
        ct = Table(call_table_data, colWidths=[0.8 * cm, 4.5 * cm, 2.2 * cm, 2 * cm, 4 * cm, 3 * cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(ct)
        if len(call_logs) > 100:
            story.append(Paragraph(f"... and {len(call_logs)-100} more records (see database for full list)", small))
    else:
        story.append(Paragraph("No call log records extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 3: SMS / MMS ----
    story.append(Paragraph("3. SMS / MMS MESSAGES", h1))
    if sms_messages:
        sms_table = [["#", "Address / Contact", "Type", "Message (excerpt)", "Date / Time"]]
        for i, s in enumerate(sms_messages[:100], 1):
            body = (s.get("body") or "")[:80].replace("\n", " ")
            ts = s.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts or "")
            tag = "MMS" if s.get("is_mms") else s.get("sms_type", "sms").upper()
            sms_table.append([
                str(i),
                f"{s.get('address','')}\n{s.get('contact_name','')}",
                tag,
                body,
                ts_str,
            ])
        smt = Table(sms_table, colWidths=[0.8 * cm, 3.5 * cm, 1.5 * cm, 8 * cm, 3.5 * cm])
        smt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(smt)
    else:
        story.append(Paragraph("No SMS/MMS records extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 4: CONTACTS ----
    story.append(Paragraph("4. CONTACTS", h1))
    if contacts:
        con_table = [["#", "Name", "Phone Numbers", "Emails", "Organization"]]
        for i, c in enumerate(contacts[:80], 1):
            phones = c.get("phone_numbers")
            if isinstance(phones, str):
                import json as _json
                try:
                    phones = ", ".join(_json.loads(phones))
                except Exception:
                    pass
            elif isinstance(phones, list):
                phones = ", ".join(phones)
            emails_val = c.get("emails")
            if isinstance(emails_val, str):
                import json as _json
                try:
                    emails_val = ", ".join(_json.loads(emails_val))
                except Exception:
                    pass
            elif isinstance(emails_val, list):
                emails_val = ", ".join(emails_val)
            con_table.append([str(i), c.get("name",""), str(phones or ""), str(emails_val or ""), c.get("organization","") or ""])
        cont = Table(con_table, colWidths=[0.8 * cm, 4 * cm, 4.5 * cm, 4 * cm, 3 * cm])
        cont.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(cont)
    else:
        story.append(Paragraph("No contact records extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 5: MEDIA FILES ----
    story.append(Paragraph("5. MEDIA FILES", h1))
    if media_files:
        med_table = [["#", "Filename", "Type", "Size (KB)", "GPS Coords", "Camera", "Date / Time"]]
        for i, m in enumerate(media_files[:80], 1):
            gps = ""
            if m.get("gps_latitude") and m.get("gps_longitude"):
                gps = f"{m['gps_latitude']:.4f}, {m['gps_longitude']:.4f}"
            ts = m.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts or "")
            size_kb = round((m.get("file_size") or 0) / 1024, 1)
            camera = f"{m.get('camera_make','')} {m.get('camera_model','')}".strip()
            med_table.append([
                str(i),
                (m.get("filename",""))[:40],
                m.get("file_type",""),
                str(size_kb),
                gps,
                camera[:25],
                ts_str,
            ])
        mt = Table(med_table, colWidths=[0.8*cm, 4*cm, 1.5*cm, 1.8*cm, 3.5*cm, 3*cm, 3*cm])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(mt)
        # Embed thumbnails for photos
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Photo Thumbnails:", h2))
        thumbs = [m for m in media_files if m.get("thumbnail_path") and os.path.exists(str(m.get("thumbnail_path","")))]
        if thumbs:
            row = []
            img_rows = []
            for m in thumbs[:24]:  # max 24 thumbnails
                try:
                    img = RLImage(m["thumbnail_path"], width=3.5 * cm, height=3.5 * cm)
                    row.append(img)
                    if len(row) == 4:
                        img_rows.append(row)
                        row = []
                except Exception:
                    pass
            if row:
                row += [""] * (4 - len(row))
                img_rows.append(row)
            if img_rows:
                thumb_t = Table(img_rows, colWidths=[4 * cm] * 4)
                thumb_t.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GRAY),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(thumb_t)
    else:
        story.append(Paragraph("No media files extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 6: APP DATA ----
    story.append(Paragraph("6. APP DATA (WhatsApp, Browser, etc.)", h1))
    if app_data:
        app_table = [["#", "App", "Type", "From", "To", "Content (excerpt)", "Time"]]
        for i, a in enumerate(app_data[:80], 1):
            content = (a.get("content") or "")[:60].replace("\n", " ")
            ts = a.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts or "")
            app_table.append([
                str(i), a.get("app_name",""), a.get("data_type",""),
                (a.get("sender",""))[:20], (a.get("recipient",""))[:20], content, ts_str
            ])
        at = Table(app_table, colWidths=[0.7*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 5*cm, 2.5*cm])
        at.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(at)
    else:
        story.append(Paragraph("No app data extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 7: EMAILS ----
    story.append(Paragraph("7. EMAILS", h1))
    if emails:
        em_table = [["#", "From", "To", "Subject", "Date"]]
        for i, e in enumerate(emails[:60], 1):
            ts = e.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts or "")
            to_list = e.get("recipients", [])
            if isinstance(to_list, str):
                try:
                    import json as _json
                    to_list = _json.loads(to_list)
                except Exception:
                    to_list = [to_list]
            em_table.append([
                str(i), (e.get("sender",""))[:30], ", ".join(to_list)[:30],
                (e.get("subject",""))[:50], ts_str
            ])
        emt = Table(em_table, colWidths=[0.8*cm, 4*cm, 4*cm, 6*cm, 3*cm])
        emt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(emt)
    else:
        story.append(Paragraph("No email records extracted.", normal))
    story.append(PageBreak())

    # ---- SECTION 8: CHAIN OF CUSTODY ----
    story.append(Paragraph("8. CHAIN OF CUSTODY / AUDIT LOG", h1))
    story.append(Paragraph(
        "The following log records every action taken on this evidence, forming the digital chain of custody.",
        normal
    ))
    if audit_logs:
        aud_table = [["#", "Timestamp (UTC)", "Action", "Actor", "Details"]]
        for i, a in enumerate(audit_logs, 1):
            ts = a.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts or "")
            aud_table.append([
                str(i), ts_str, a.get("action",""),
                a.get("actor","system"), (a.get("details",""))[:80]
            ])
        audt = Table(aud_table, colWidths=[0.8*cm, 3.5*cm, 3.5*cm, 2.5*cm, 7*cm])
        audt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(audt)
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("END OF REPORT", center))
    story.append(Paragraph("This document is confidential and for official forensics use only.", small))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
