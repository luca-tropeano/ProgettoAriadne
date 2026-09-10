"""Ariadne Web UI — import BOM, visualizzazione, export, statistiche.

Interfaccia web (Flask) che usa la stessa pipeline del CLI ma su browser:
- Import di file BOM (xlsx/ods/csv/pdf/html) con campi dispositivo
- Elenco devices e relativi componenti (con EEC)
- Esportazione Excel di un device
- Statistiche

Il DB resta SQLite locale (stessa sede della CLI). Strapi/PostgreSQL NON è
necessario: la UI lavora sui dati locali, e la sincronizzazione verso Strapi
è un'operazione separata (strapi_client).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for

from ariadne.bom_diff import diff_boms
from ariadne.config import AppConfig
from ariadne.database import Database
from ariadne.export import eec_name, export_device_to_excel
from ariadne.models import Device
from ariadne.orchestrator import Orchestrator
from ariadne.resellers import reseller_links

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".xlsx", ".xls", ".ods", ".csv", ".pdf", ".html", ".htm", ".md", ".markdown"}


def create_app(config: AppConfig | None = None) -> Flask:
    config = config or AppConfig.from_env()
    app = Flask(__name__)
    app.secret_key = "ariadne-dev-secret"
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

    @app.errorhandler(413)
    def too_large(_e):
        flash("File troppo grande: il limite è 25 MB.", "error")
        return redirect(url_for("index"))

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
            missing = [n for n, v in (("brand", brand), ("model", model),
                                      ("manufacturer", manufacturer)) if not v]
            if missing:
                flash(
                    "Campi obbligatori mancanti per l'import: "
                    + ", ".join(missing) + ".",
                    "error",
                )
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
                # recap differenze: stato precedente del prodotto (se già importato)
                existing = None
                prev_entries = []
                new_entries = []
                try:
                    parsed = orch.parse_entries(str(saved))
                    new_entries = orch.entries_to_dicts(parsed)
                except Exception:
                    new_entries = []
                if new_entries:
                    pre = Database(config.database)
                    try:
                        existing = pre.get_device_by_model(device.model_name)
                        if existing:
                            prev_entries = pre.get_bom_entries(existing["id"])
                    finally:
                        pre.close()
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
            if (
                new_entries and existing and result.success
                and orch.latest_device_id == existing["id"]
            ):
                recap = diff_boms(prev_entries, new_entries)
                if recap.has_changes:
                    session["bom_recap"] = {
                        "model_name": existing["model_name"],
                        "imported_rows": result.imported_rows,
                        **recap.as_dict(),
                    }
                    return redirect(
                        url_for("device_recap", device_id=existing["id"])
                    )
            if orch.latest_device_id:
                return redirect(url_for("device_detail", device_id=orch.latest_device_id))
            return redirect(url_for("index"))
        return render_template("import.html", allowed=", ".join(sorted(e.lstrip('.') for e in ALLOWED_EXT)))

    @app.route("/device/<int:device_id>/recap")
    def device_recap(device_id: int):
        recap = session.pop("bom_recap", None)
        db = Database(config.database)
        try:
            device = db.get_device_by_id(device_id)
            if not recap or not device:
                if not device:
                    flash("Device non trovato.", "error")
                    return redirect(url_for("index"))
                return redirect(url_for("device_detail", device_id=device_id))
            return render_template("recap.html", device=device, recap=recap)
        finally:
            db.close()

    @app.route("/device/<int:device_id>/edit", methods=["GET", "POST"])
    def device_edit(device_id: int):
        db = Database(config.database)
        try:
            device = db.get_device_by_id(device_id)
            if not device:
                flash("Device non trovato.", "error")
                return redirect(url_for("index"))
            if request.method == "POST":
                brand = request.form.get("brand", "").strip()
                model_name = request.form.get("model", "").strip()
                manufacturer = request.form.get("manufacturer", "").strip()
                year = request.form.get("year", "").strip()
                notes = request.form.get("notes", "").strip()
                missing = [n for n, v in (("brand", brand), ("model", model_name),
                                          ("manufacturer", manufacturer)) if not v]
                if missing:
                    flash(
                        "Campi obbligatori mancanti: " + ", ".join(missing) + ".",
                        "error",
                    )
                    return render_template("device_edit.html", device=device)
                try:
                    updated = db.update_device(
                        device_id,
                        brand=brand,
                        model_name=model_name,
                        manufacturer=manufacturer,
                        year_of_production=int(year) if year.isdigit() else None,
                        notes=notes,
                    )
                except sqlite3.IntegrityError:
                    flash(f"Esiste già un device con modello '{model_name}'.", "error")
                    return render_template("device_edit.html", device=device)
                if not updated:
                    flash("Device non trovato.", "error")
                    return redirect(url_for("index"))
                flash("Device aggiornato.", "success")
                return redirect(url_for("device_detail", device_id=device_id))
            return render_template("device_edit.html", device=device)
        finally:
            db.close()

    @app.route("/device/<int:device_id>/delete", methods=["POST"])
    def device_delete(device_id: int):
        db = Database(config.database)
        try:
            if not db.get_device_by_id(device_id):
                flash("Device non trovato.", "error")
                return redirect(url_for("index"))
            db.delete_device(device_id)
            flash("Device eliminato.", "success")
            return redirect(url_for("index"))
        finally:
            db.close()

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
                e["_links"] = reseller_links(
                    e.get("manufacturer_order_code") or e.get("supplier_order_code")
                )
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

    @app.route("/materials")
    def materials():
        db = Database(config.database)
        try:
            materials = db.get_materials()
            links = db.get_component_material_links()
            for l in links:
                l["_links"] = reseller_links(
                    l.get("manufacturer_order_code") or l.get("supplier_order_code")
                )
            return render_template("materials.html", materials=materials, links=links)
        finally:
            db.close()

    @app.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
    def entry_edit(entry_id: int):
        db = Database(config.database)
        try:
            entry = db.get_bom_entry_by_id(entry_id)
            if not entry:
                flash("Componente non trovato.", "error")
                return redirect(url_for("index"))
            device = db.get_device_by_id(entry["device_id"])
            device = device or {"id": 0, "model_name": "—"}
            if request.method == "POST":
                fields = {
                    "item_number": request.form.get("item_number", "").strip(),
                    "quantity": request.form.get("quantity", "").strip(),
                    "reference_designator": request.form.get("reference_designator", "").strip(),
                    "part_value": request.form.get("part_value", "").strip(),
                    "package": request.form.get("package", "").strip(),
                    "manufacturer": request.form.get("manufacturer", "").strip(),
                    "manufacturer_order_code": request.form.get("manufacturer_order_code", "").strip(),
                    "supplier": request.form.get("supplier", "").strip(),
                    "supplier_order_code": request.form.get("supplier_order_code", "").strip(),
                    "mounting_type": request.form.get("mounting_type", "SMT").strip(),
                    "notes": request.form.get("notes", "").strip(),
                }
                missing = [n for n, v in (("item_number", fields["item_number"]),
                                          ("quantity", fields["quantity"]),
                                          ("reference_designator", fields["reference_designator"])) if not v]
                if missing:
                    flash("Campi obbligatori mancanti: " + ", ".join(missing) + ".", "error")
                    return render_template("entry_edit.html", entry=entry, device=device)
                try:
                    fields["item_number"] = int(fields["item_number"])
                    fields["quantity"] = int(fields["quantity"])
                except ValueError:
                    flash("item number e quantità devono essere numerici.", "error")
                    return render_template("entry_edit.html", entry=entry, device=device)
                db.update_bom_entry(entry_id, **fields)
                flash("Componente aggiornato.", "success")
                return redirect(url_for("device_detail", device_id=entry["device_id"]))
            return render_template("entry_edit.html", entry=entry, device=device)
        finally:
            db.close()

    return app


def main():
    app = create_app()
    print("Ariadne Web UI: http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
