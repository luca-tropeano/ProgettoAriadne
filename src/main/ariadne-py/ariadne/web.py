"""Ariadne Web UI — import BOM, visualizzazione, export, statistiche.

Interfaccia web (Flask) che usa la stessa pipeline del CLI ma su browser:
- Import di file BOM (xlsx/ods/csv/pdf) con campi dispositivo
- Elenco devices e relativi componenti (con EEC)
- Esportazione Excel di un device
- Statistiche

Il DB resta SQLite locale (stessa sede della CLI). Strapi/PostgreSQL NON è
necessario: la UI lavora sui dati locali, e la sincronizzazione verso Strapi
è un'operazione separata (strapi_client).
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from ariadne.config import AppConfig
from ariadne.database import Database
from ariadne.export import eec_name, export_device_to_excel
from ariadne.models import Device
from ariadne.orchestrator import Orchestrator

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".xlsx", ".xls", ".ods", ".csv", ".pdf"}


def create_app(config: AppConfig | None = None) -> Flask:
    config = config or AppConfig.from_env()
    app = Flask(__name__)
    app.secret_key = "ariadne-dev-secret"
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

    @app.context_processor
    def inject_stats():
        db = Database(config.database)
        try:
            return {"nav_stats": db.get_stats()}
        finally:
            db.close()

    @app.route("/")
    def index():
        db = Database(config.database)
        try:
            devices = db.get_all_devices()
            return render_template("index.html", devices=devices)
        finally:
            db.close()

    @app.route("/api/stats")
    def api_stats():
        db = Database(config.database)
        try:
            return db.get_stats()
        finally:
            db.close()

    @app.route("/import", methods=["GET", "POST"])
    def import_bom():
        if request.method == "POST":
            brand = request.form.get("brand", "").strip()
            model = request.form.get("model", "").strip()
            manufacturer = request.form.get("manufacturer", "").strip()
            year = request.form.get("year", "").strip()
            file = request.files.get("bom_file")
            if not file or not file.filename:
                flash("Seleziona un file BOM.", "error")
                return redirect(url_for("import_bom"))
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXT:
                flash(f"Formato non supportato: {ext}", "error")
                return redirect(url_for("import_bom"))

            saved = UPLOAD_DIR / file.filename
            file.save(saved)
            device = Device(
                brand=brand,
                model_name=model or Path(file.filename).stem,
                manufacturer=manufacturer or brand,
                year_of_production=int(year) if year.isdigit() else None,
            )
            orch = Orchestrator(config)
            try:
                result = orch.process_file(str(saved), device)
            finally:
                orch.close()
            if result.success:
                flash(
                    f"Import riuscito: {result.imported_rows} componenti su "
                    f"{result.total_rows}.",
                    "success",
                )
            else:
                flash(
                    f"Import con errori: {result.failed_rows} righe fallite su "
                    f"{result.total_rows}.",
                    "error",
                )
            if orch.latest_device_id:
                return redirect(url_for("device_detail", device_id=orch.latest_device_id))
            return redirect(url_for("index"))
        return render_template("import.html", allowed=", ".join(sorted(e.lstrip('.') for e in ALLOWED_EXT)))

    @app.route("/device/<int:device_id>")
    def device_detail(device_id: int):
        db = Database(config.database)
        try:
            device = db.get_device_by_id(device_id)
            if not device:
                flash("Device non trovato.", "error")
                return redirect(url_for("index"))
            entries = db.get_bom_entries(device_id)
            for e in entries:
                e["_eec_name"] = eec_name(e.get("eec_category_id"))
            return render_template("device.html", device=device, entries=entries)
        finally:
            db.close()

    @app.route("/device/<int:device_id>/export")
    def export_device(device_id: int):
        db = Database(config.database)
        try:
            device = db.get_device_by_id(device_id)
            if not device:
                flash("Device non trovato.", "error")
                return redirect(url_for("index"))
            out = export_device_to_excel(db, device_id, str(UPLOAD_DIR / f"device_{device_id}.xlsx"))
            return send_file(out, as_attachment=True, download_name=f"{device['model_name']}_bom.xlsx")
        finally:
            db.close()

    return app


def main():
    app = create_app()
    print("Ariadne Web UI: http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
