# BOM Import Pipeline — Specifica Tecnica

**VERSIONE: 1.5** | **Data:** 29/07/2026 | **Autore:** Tropeano Luca

## Panoramica

Pipeline Python (CLI) per importare file BOM da Excel (.xlsx) e da PDF (via DeepSeek AI), scrivendo i dati su SQLite (locale) e/o Strapi API.

**Flussi supportati:**
- **Excel (.xlsx)** → openpyxl parser → SQLite / Strapi API
- **PDF (.pdf)** → pdfplumber text extraction → DeepSeek AI API → JSON → SQLite / Strapi API

## Struttura del Progetto

```
ariadne-py/
├── pyproject.toml                  # Python 3.11+, dipendenze pip
├── .env.example                    # Template configurazione
├── ariadne/
│   ├── __init__.py
│   ├── main.py                     # CLI entry point (click)
│   ├── config.py                   # AppConfig, DeepSeekConfig, StrapiConfig, SFTPConfig, DatabaseConfig
│   ├── models.py                   # BOMEntry, Device, Material, ComponentMaterial, ImportResult (pydantic)
│   ├── database.py                 # Wrapper SQLite
│   ├── excel_parser.py             # Parsing Excel (openpyxl)
│   ├── pdf_extractor.py            # Estrazione testo PDF (pdfplumber)
│   ├── ai_client.py                # Client DeepSeek (OpenAI-compatibile)
│   ├── orchestrator.py             # Orchestrator — coordinamento processi
│   └── sftp_client.py              # Upload SFTP (paramiko)
└── tests/
    ├── __init__.py
    ├── test_excel_parser.py         # pytest — parser Excel
    ├── test_ai_client.py            # pytest — risposte DeepSeek
    └── test_models.py               # pytest — modelli pydantic
```

## main.py — CLI Entry Point (click)

```python
import click
from ariadne.config import AppConfig
from ariadne.models import Device
from ariadne.orestrator import Orchestrator

@click.group()
def cli():
    """Ariadne — BOM processing pipeline."""
    pass

@cli.command()
@click.argument("file_path")
@click.option("--brand", default="", help="Device brand")
@click.option("--model", default="", help="Device model name")
@click.option("--manufacturer", default="", help="Device manufacturer")
@click.option("--year", type=int, default=None, help="Year of production")
@click.pass_context
def process(ctx, file_path, brand, model, manufacturer, year):
    """Process a BOM file (Excel or PDF)."""
    cfg = AppConfig.from_env()
    orch = Orchestrator(cfg)
    device = Device(brand=brand, model_name=model,
                    manufacturer=manufacturer, year_of_production=year)
    result = orch.process_file(file_path, device)
    click.echo(f"\nResults:\n  Total:     {result.total_rows}\n"
               f"  Imported:  {result.imported_rows}\n"
               f"  Failed:    {result.failed_rows}")
    for w in result.warnings:
        click.echo(f"  [WARN] {w}")
    for e in result.errors:
        click.echo(f"  [ERROR] {e}")

@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    cfg = AppConfig.from_env()
    orch = Orchestrator(cfg)
    s = orch.get_stats()
    click.echo(f"Devices:     {s['devices']}")
    click.echo(f"BOM Entries: {s['bom_entries']}")
    click.echo(f"Materials:   {s['materials']}")
```

**Auto-rilevamento formato:** Estensione file determina il flusso: `.xlsx` → Excel, `.pdf` → PDF.

## Orchestrator — Coordinatore

File: `ariadne/orestrator.py`

```python
class Orchestrator:
    def __init__(self, config: AppConfig):
        self.cfg = config
        self.db = Database(config.database.url)

    def process_file(self, file_path: str, device: Device) -> ImportResult:
        ext = Path(file_path).suffix.lower()
        if ext == ".xlsx":
            return self._process_excel(file_path, device)
        elif ext == ".pdf":
            return self._process_pdf(file_path, device)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _process_excel(self, file_path, device):
        entries = parse_excel_bom(file_path)
        return self._import_entries(entries, device)

    def _process_pdf(self, file_path, device):
        text = extract_text_from_pdf(file_path)
        client = DeepSeekClient(self.cfg.deepseek)
        entries = client.extract_bom(text)
        return self._import_entries(entries, device)

    def _import_entries(self, entries, device) -> ImportResult:
        result = ImportResult(total_rows=len(entries))
        device_id = self.db.find_or_create_device(device)
        for entry in entries:
            try:
                self.db.insert_bom_entry(device_id, entry)
                result.imported_rows += 1
            except Exception as e:
                result.failed_rows += 1
                result.errors.append(str(e))
        return result
```

## excel_parser.py — Parsing Excel

File: `ariadne/excel_parser.py`

- Usa **openpyxl** per leggere file `.xlsx`
- Header row 6, dati da riga 7
- 17 colonne mappate su `BOMEntry` (10 campi)
- Rilevamento automatico SMT/THT: DIP/SIP/TO- → THT, altrimenti SMT
- Converte automaticamente valori int/float celle in stringhe

```python
def parse_excel_bom(file_path: str) -> list[BOMEntry]:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    entries = []
    for row in ws.iter_rows(min_row=7, values_only=False):
        if row[0].value is None:
            continue
        try:
            item_number = int(row[0].value)
            quantity = int(row[1].value)
        except (ValueError, TypeError):
            continue
        if not row[2].value:
            continue
        entries.append(BOMEntry(
            item_number=item_number,
            quantity=quantity,
            reference_designator=str(row[2].value),
            part_value=_str(row[4].value),
            package=_str(row[8].value),
            manufacturer=_str(row[9].value),
            manufacturer_order_code=_str(row[10].value),
            supplier=_str(row[12].value),
            supplier_order_code=_str(row[13].value),
            notes=_str(row[11].value),
            mounting_type=_detect_mounting_type(_str(row[8].value)),
        ))
    wb.close()
    return entries
```

## pdf_extractor.py — Estrazione PDF

File: `ariadne/pdf_extractor.py`

- Usa **pdfplumber** per estrazione testo nativa
- `extract_text_from_pdf(path)` → testo separato per pagina
- `extract_text_from_pdf_stream(stream)` → variante per stream
- Non gestisce PDF scannerizzati/immagine

## ai_client.py — DeepSeek Client

File: `ariadne/ai_client.py`

- Comunica con API DeepSeek (`/v1/chat/completions`, formato OpenAI)
- `extract_bom(text, system_prompt=None)` → `list[BOMEntry]`
- System prompt specializzato per estrazione BOM in italiano
- Parsing robusto: `json.loads()` diretto → fallback blocco ```json
- Configurabile via `.env`

```python
class DeepSeekClient:
    def __init__(self, config: DeepSeekConfig):
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url

    def extract_bom(self, text: str, system_prompt: str | None = None) -> list[BOMEntry]:
        response = self._call_api(text, system_prompt)
        return self._parse_response(response)
```

## database.py — Wrapper SQLite

File: `ariadne/database.py`

- Usa `sqlite3` (standard library)
- Schema: `device` (id, brand, model_name, manufacturer, year_of_production, notes)
- Schema: `bom_entry` (id, device_id FK, item_number, quantity, reference_designator, part_value, package, manufacturer, manufacturer_order_code, supplier, supplier_order_code, notes, mounting_type, designator_code, eec_category_id)
- `find_or_create_device(device)` → device_id
- `insert_bom_entry(device_id, entry)` → entry_id
- `get_stats()` → dict (device, bom_entry, material counts)

## Modelli Dati (Pydantic)

File: `ariadne/models.py`

```python
class BOMEntry(BaseModel):
    item_number: int
    quantity: int
    reference_designator: str
    part_value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    manufacturer_order_code: str | None = None
    supplier: str | None = None
    supplier_order_code: str | None = None
    notes: str | None = None
    mounting_type: str = "SMT"
    designator_code: str | None = None
    eec_category_id: int | None = None

class Device(BaseModel):
    brand: str = ""
    model_name: str = ""
    manufacturer: str = ""
    year_of_production: int | None = None
    notes: str | None = None

class ImportResult(BaseModel):
    total_rows: int = 0
    imported_rows: int = 0
    failed_rows: int = 0
    success: bool = True  # calcolato: success = (failed_rows == 0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
```

## Configurazione (.env)

```env
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL=deepseek-chat
# STRAPI_BASE_URL=http://localhost:1337
# STRAPI_API_TOKEN=
# SFTP_HOST=
# SFTP_PORT=22
# SFTP_USER=
# SFTP_PASSWORD=
# SFTP_REMOTE_PATH=/uploads
# DATABASE_URL=sqlite:///ariadne.db
```

## Dipendenze (pyproject.toml)

```toml
dependencies = [
    "pdfplumber>=0.11",
    "openpyxl>=3.1",
    "httpx>=0.27",
    "paramiko>=3.4",
    "pydantic>=2.7",
    "click>=8.1",
    "python-dotenv>=1.0",
]
[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
```

## Test (pytest)

```bash
cd src/main/ariadne-py
pip install -e ".[dev]"
pytest tests/ --verbose
```

**11 test, tutti passanti.**

| File | # Test | Cosa verifica |
|------|--------|---------------|
| test_models.py | 6 | BOMEntry, Device, ImportResult |
| test_excel_parser.py | 3 | SMT/THT detection |
| test_ai_client.py | 3 | DeepSeek JSON parsing |

## CLI Usage

```bash
ariadne process "BOM.xlsx" --brand STM --model STEVAL-SPIN3204
ariadne process "BOM.pdf" --brand STM --model STEVAL-SPIN3204
ariadne stats
```

## Excel Column Mapping (17-colonne)

| Col | Header | Campo | Note |
|-----|--------|-------|------|
| 1 | Item | item_number | int — salta righe non numeriche |
| 2 | Qty | quantity | int |
| 3 | Reference | reference_designator | Testo diretto |
| 5 | Part/Value | part_value | Valore componente |
| 9 | Package | mounting_type | DIP/SIP/TO- → THT, altrimenti SMT |
| 10 | Manufacturer | manufacturer | Produttore |
| 11 | Mfr Order Code | manufacturer_order_code | Stringa |
| 12 | Notes | notes | Note |
| 13 | Supplier | supplier | Primo fornitore |
| 14 | Supplier Code | supplier_order_code | Codice fornitore |

**Risultato reale:** 74/74 righe importate (identico al precedente import C#).
