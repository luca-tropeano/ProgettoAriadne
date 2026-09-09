from __future__ import annotations

import sys
from pathlib import Path

import click

from ariadne.config import AppConfig
from ariadne.models import BOMEntry, Device
from ariadne.orchestrator import Orchestrator


@click.group()
@click.pass_context
def cli(ctx):
    """Ariadne — BOM processing pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = AppConfig.from_env()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--brand", default="", help="Device brand")
@click.option("--model", default="", help="Device model name")
@click.option("--manufacturer", default="", help="Device manufacturer")
@click.option("--year", default=0, type=int, help="Year of production")
@click.pass_context
def process(ctx, file_path: str, brand: str, model: str, manufacturer: str, year: int):
    """Process a BOM file (Excel or PDF)."""
    config = ctx.obj["config"]
    device = Device(
        brand=brand,
        model_name=model,
        manufacturer=manufacturer or brand,
        year_of_production=year or None,
    )

    click.echo(f"Processing: {file_path}")
    click.echo(f"Device: {brand} {model}")

    orch = Orchestrator(config)
    try:
        result = orch.process_file(file_path, device)
    finally:
        orch.close()

    click.echo(f"\nResults:")
    click.echo(f"  Total:     {result.total_rows}")
    click.echo(f"  Imported:  {result.imported_rows}")
    click.echo(f"  Failed:    {result.failed_rows}")

    for w in result.warnings:
        click.echo(f"  [WARN] {w}")
    for e in result.errors:
        click.echo(f"  [ERROR] {e}", err=True)

    sys.exit(0 if result.success else 1)


@cli.command()
@click.option("--model", default="", help="Sync only this device model")
@click.option("--materials", is_flag=True, default=False,
              help="Sincronizza anche i materiali (MDF) collegati alle BOMEntry")
@click.pass_context
def strapi_sync(ctx, model: str, materials: bool):
    """Sincronizza i device (e BOM entries) verso Strapi via REST.

    Con ``--materials`` carica anche i materiali MDF: ogni materiale viene
    upsertato su ``materials`` e ogni link viene creato su ``component-materials``
    (relazione materiale ↔ BOMEntry). Richiede l'id Strapi della BOMEntry appena
    creata, restituito da ``sync_device`` in ``entry_strapi_ids`` nello stesso
    ordine delle entries locali.
    """
    config = ctx.obj["config"]
    if not config.strapi.api_token:
        click.echo("STRAPI_API_TOKEN non configurato. Impostare .env: STRAPI_API_TOKEN=...")
        raise SystemExit(1)

    from ariadne.models import Material
    from ariadne.strapi_client import StrapiClient

    client = StrapiClient(config.strapi.base_url, config.strapi.api_token)
    orch = Orchestrator(config)
    try:
        devices = orch.get_all_devices()
        if model:
            devices = [d for d in devices if d["model_name"] == model]
        if not devices:
            click.echo("Nessun device da sincronizzare.")
            return
        for dev_row in devices:
            device = Device(
                brand=dev_row["brand"],
                model_name=dev_row["model_name"],
                manufacturer=dev_row["manufacturer"],
                year_of_production=dev_row["year_of_production"],
                notes=dev_row["notes"],
            )
            rows = orch.get_bom_entries(dev_row["id"])
            entries = [
                BOMEntry(**{k: e[k] for k in BOMEntry.model_fields if k in e})
                for e in rows
            ]
            res = client.sync_device(device, entries)
            click.echo(f"  {dev_row['model_name']}: device id={res['device_id']}, entries={res['entries_pushed']}")
            if not materials:
                continue
            sid_by_db_id = {
                row["id"]: sid
                for row, sid in zip(rows, res["entry_strapi_ids"])
            }
            links = orch.get_component_material_links(dev_row["id"])
            pushed = 0
            for link in links:
                entry_sid = sid_by_db_id.get(link["bom_entry_id"])
                if entry_sid is None:
                    continue
                material = Material(
                    material_name=link["material_name"],
                    casrn=link["casrn"],
                    category=link["category"],
                )
                material_sid = client.upsert_material(material)
                client.push_component_material(
                    entry_sid,
                    material_sid,
                    mass_mg=link["mass_mg"],
                    note=link["note"],
                    source_mdf=link["source_mdf"],
                )
                pushed += 1
            click.echo(f"    materials: {pushed} link sincronizzati")
    finally:
        client.close()
        orch.close()


@cli.command()
@click.argument("mdf_file", type=click.Path(exists=True))
@click.pass_context
def mdf_ingest(ctx, mdf_file: str):
    """Popola i materiali da un file MDF (JSON ad-hoc, XML IPC-1752 Class D o PDF).

    Il file grezzo viene archiviato in MongoDB (se disponibile) prima del parse.
    """
    config = ctx.obj["config"]
    orch = Orchestrator(config)
    try:
        suffix = Path(mdf_file).suffix.lower()
        try:
            res = orch.ingest_mdf(mdf_file)
        except NotImplementedError as e:
            click.echo(f"[STUB] {e}")
            return
        label = {
            ".json": "JSON",
            ".xml": "XML (IPC-1752A/B class D)",
            ".pdf": "PDF (Material Declaration, pdfplumber)",
        }.get(suffix, suffix)
        click.echo(f"MDF ingestione ({label}):")
        click.echo(f"  Materiali creati:     {res.materials_created}")
        click.echo(f"  Materiali saltati:    {res.materials_skipped}")
        click.echo(f"  Link creati:          {res.links_created}")
        click.echo(f"  Link saltati:         {res.links_skipped}")
        for w in res.warnings:
            click.echo(f"  [WARN] {w}")
    finally:
        orch.close()


@cli.command()
@click.argument("part_number")
@click.option("--out-dir", default="mdf_downloads", show_default=True,
              help="Cartella dove salvare l'XML MDF scaricato")
@click.option("--source", default="auto", show_default=True,
              help="Portale: murata | digikey | mouser | bomcheck | octopart | url:https://...")
@click.pass_context
def mdf_download(ctx, part_number: str, out_dir: str, source: str):
    """Scarica l'MDF (IPC-1752 XML) di un part number dai portali pubblici.

    Percorso ONLINE (opzionale): i portali non espongono API documentate, quindi
    il downloader visita le pagine di ricerca, estrae i link candidati e prova a
    parsare quelli XML come IPC-1752 Class D. Richiede rete; la demo resta offline.
    """
    from ariadne.mdf_portal import MDFPortalDownloader

    config = ctx.obj["config"]
    downloader = MDFPortalDownloader()
    try:
        result = downloader.download(part_number, out_dir=out_dir, source=source)
    finally:
        downloader.close()
    if result.downloaded is not None:
        click.echo(f"Downloaded: {result.downloaded}")
        click.echo(f"  Part number: {result.part_number}")
    else:
        click.echo(f"Nessun MDF valido trovato per '{part_number}' (source={source}).")
    for url in result.found:
        click.echo(f"  [candidato non valido] {url}")
    for e in result.errors:
        click.echo(f"  [ERROR] {e}", err=True)
    sys.exit(0 if result.downloaded is not None else 1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    config = ctx.obj["config"]
    orch = Orchestrator(config)
    try:
        s = orch.get_stats()
    finally:
        orch.close()

    click.echo(f"Devices:       {s['devices']}")
    click.echo(f"BOM Entries:   {s['bom_entries']}")
    click.echo(f"Materials:     {s['materials']}")
    raw_available = s.get("raw_available", False)
    click.echo(f"Raw docs (MongoDB): {s.get('raw_documents', 0)} ({'online' if raw_available else 'offline'})")


if __name__ == "__main__":
    cli()
