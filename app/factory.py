"""Flask application factory."""
import os
from flask import Flask, send_from_directory

from app.config import Config
from app.routes import (auth_bp, identity_records_bp, data_users_bp,
                         data_providers_bp, webhooks_bp, portal_dcc_bp,
                         admin_bp, self_service_bp)
from app import db as database


def create_app(config_class=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    for bp in (auth_bp, identity_records_bp, data_users_bp,
               data_providers_bp, webhooks_bp, portal_dcc_bp,
               admin_bp, self_service_bp):
        app.register_blueprint(bp)

    # Serve UI pages as static files
    ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")

    @app.route("/admin")
    @app.route("/admin/")
    def admin_ui():
        return send_from_directory(os.path.join(ui_dir, "admin"), "index.html")

    @app.route("/dashboard")
    @app.route("/dashboard/")
    def dashboard_ui():
        return send_from_directory(os.path.join(ui_dir, "dashboard"), "index.html")

    @app.route("/portal")
    @app.route("/portal/")
    def portal_ui():
        return send_from_directory(os.path.join(ui_dir, "portal"), "index.html")

    @app.route("/ui/lib/<path:filename>")
    def ui_lib(filename):
        return send_from_directory(os.path.join(ui_dir, "lib"), filename)

    with app.app_context():
        try:
            database.init_db()
        except Exception as e:
            app.logger.warning(f"DB init skipped (CouchDB not available): {e}")

    return app
