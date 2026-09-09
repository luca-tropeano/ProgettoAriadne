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
@click.pass_context
def strapi_sync(ctx, model: str):
    """Sincronizza i device (e BOM entries) verso Strapi via REST."""
    config = ctx.obj["config"]
    if not config.strapi.api_token:
        click.echo("STRAPI_API_TOKEN non configurato. Impostare .env: STRAPI_API_TOKEN=...")
        raise SystemExit(1)

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
            entries = [
                BOMEntry(**{k: e[k] for k in BOMEntry.model_fields if k in e})
                for e in orch.get_bom_entries(dev_row["id"])
            ]
            res = client.sync_device(device, entries)
            click.echo(f"  {dev_row['model_name']}: device id={res['device_id']}, entries={res['entries_pushed']}")
    finally:
        client.close()
        orch.close()


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
