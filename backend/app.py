"""
Main Flask Application Entry Point
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes import cases_bp, devices_bp, evidence_bp, reports_bp, audit_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"])

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(cases_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(audit_bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "forensic-backend"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
