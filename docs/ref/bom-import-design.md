# BOM Import Pipeline — Specifica Tecnica

**VERSIONE: 1.11** | **Data:** 09/09/2026 | **Autore:** Tropeano Luca

## Panoramica

Pipeline Python (CLI) per importare file BOM da Excel (.xlsx), OpenDocument (.ods), CSV, PDF e KiCad InteractiveHtmlBom (.html), classificare i componenti (EEC 16 categorie), controllare duplicati, esportare in Excel e archiviare i dati grezzi in MongoDB.

**Flussi supportati:**
- **Excel (.xlsx)** → openpyxl parser → SQLite / Strapi API
- **OpenDocument (.ods)** → ods_parser (schema dinamico, header per nome colonna) → SQLite / Strapi API
- **CSV** (KiCad/EasyEDA, `.csv`/`.txt`) → csv_parser (auto-detect delimitatore) → SQLite / Strapi API
- **PDF (.pdf) con testo estraibile** → pdfplumber → **parser diretto (regex)** → SQLite / Strapi API
- **PDF (.pdf) non riconosciuto dal parser diretto** → **DeepSeek AI (fallback, disabilitato di default)** → SQLite / Strapi API
- **PDF scannerizzato/immagine** → non ancora supportato (pianificato: OCR/AI in fasi successive)
- **KiCad InteractiveHtmlBom (`.html`/`.htm`)** → ibom_parser (LZ-String `pcbdata`, preferenza `bom.both`, fallback F/B) → SQLite / Strapi API
- **MDF (Material Data File)** → mdf_ingestor: JSON ad-hoc + **XML IPC-1752A/B Class D** (ipc1752.py) + **PDF Material Declaration** (mdf_pdf_parser.py, layout ZVEI per-componente e KEMET/YAGEO per-serie) popolano `material` + `component_material`; matching per part number

**Funzionalità trasversali:**
- Classificazione EEC automatica (16 categorie) dai reference designator
- Controllo duplicati BOM (skip con warning se già importata)
- Esportazione database → Excel (`.xlsx`) con header formattati
- **Archivio dati grezzi in MongoDB**: ogni file processato viene salvato (content + hash + metadata) prima dell'elaborazione; opzionale, graceful degradation offline

La AI DeepSeek è un **fallback a pagamento**: usata solo se il parser diretto trova 0 componenti, e solo se esplicitamente abilitata via `DEEPSEEK_ENABLED=true`.

## Struttura del Progetto

```
ariadne-py/
├── pyproject.toml                  # Python 3.11+, dipendenze pip
├── .env.example                    # Template configurazione
├── ariadne/
│   ├── __init__.py
│   ├── main.py                     # CLI entry point (click)
│   ├── web.py                      # Web UI (Flask): import, dettaglio device, export, stats
│   ├── templates/                  # Template HTML della Web UI
│   ├── config.py                   # AppConfig, DeepSeekConfig, StrapiConfig, SFTPConfig, DatabaseConfig
│   ├── models.py                   # BOMEntry, Device, Material, ComponentMaterial, ImportResult (pydantic)
│   ├── database.py                 # Wrapper SQLite
│   ├── excel_parser.py             # Parsing Excel (openpyxl)
│   ├── ods_parser.py               # Parsing OpenDocument (.ods, schema dinamico)
│   ├── csv_parser.py               # Parsing CSV (KiCad/EasyEDA, auto-detect)
│   ├── ibom_parser.py              # Parsing KiCad InteractiveHtmlBom (.html, LZ-String pcbdata)
│   ├── lzstring.py                 # Decompressore LZ-String (base64) puro-Python per IBOM
│   ├── pdf_extractor.py            # Estrazione testo PDF (pdfplumber)
│   ├── pdf_parser.py               # Parser diretto BOM da testo (regex, senza AI)
│   ├── ai_client.py                # Client DeepSeek (OpenAI-compatibile, fallback)
│   ├── orchestrator.py             # Orchestrator — coordinamento processi
│   ├── eec.py                      # Classificazione EEC 16 categorie
│   ├── export.py                   # Export database → Excel
│   ├── mongo_store.py              # Archivio dati grezzi MongoDB (opzionale)
│   ├── mdf_ingestor.py             # Ingestione MDF (JSON ad-hoc, XML IPC-1752 Class D, PDF)
│   ├── mdf_pdf_parser.py           # Parser Material Declaration PDF (pdfplumber, ZVEI/KEMET)
│   ├── ipc1752.py                  # Parser IPC-1752A/B Class D (XML materiali omogenei)
│   ├── mdf_portal.py               # Downloader MDF dai portali (ricerca + harvest XML)
│   ├── strapi_client.py            # Client Strapi REST (Device/BOMEntry/Material sync)
│   └── sftp_client.py              # Upload SFTP (paramiko)
└── tests/
    ├── __init__.py
    ├── test_excel_parser.py         # pytest — parser Excel
    ├── test_pdf_parser.py           # pytest — parser PDF diretto
    ├── test_pdf_extractor.py        # pytest — estrazione testo PDF
    ├── test_csv_parser.py           # pytest — parser CSV
    ├── test_ods_parser.py           # pytest — parser ODS
    ├── test_ibom_parser.py          # pytest — parser InteractiveHtmlBom
    ├── test_lzstring.py             # pytest — decompressore LZ-String
    ├── test_ai_client.py            # pytest — risposte DeepSeek + cost tracking
    ├── test_orchestrator.py         # pytest — flussi Excel/PDF/IBOM, AI fallback
    ├── test_new_features.py         # pytest — duplicati, EEC, export
    ├── test_mongo_store.py          # pytest — archivio raw MongoDB (online/offline)
    ├── test_strapi_client.py        # pytest — client Strapi (upsert, push, auth, materials)
    ├── test_web.py                  # pytest — Web UI (import, dettaglio, export, stats, MDF)
    ├── test_mdf_ingestor.py         # pytest — ingestione MDF (JSON + XML + PDF, link part number)
    ├── test_mdf_pdf_parser.py       # pytest — parser PDF MDF (layout ZVEI/KEMET, mg/gr)
    ├── test_mdf_portal.py           # pytest — downloader MDF dai portali (client mock)
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

**Auto-rilevamento formato:** Estensione file determina il flusso: `.xlsx` → Excel, `.ods` → ODS, `.csv` → CSV, `.pdf` → PDF, `.html`/`.htm` → IBOM. Formato non riconosciuto → errore "Unsupported format".

## Orchestrator — Coordinatore

File: `ariadne/orchestrator.py`

```python
class Orchestrator:
    def __init__(self, config: AppConfig):
        self.cfg = config
        self.db = Database(config.database)

    def process_file(self, file_path: str, device: Device) -> ImportResult:
        ext = Path(file_path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            return self._process_excel(file_path, device)
        elif ext == ".ods":
            return self._process_ods(file_path, device)
        elif ext == ".csv":
            return self._process_csv(file_path, device)
        elif ext == ".pdf":
            return self._process_pdf(file_path, device)
        elif ext in (".html", ".htm"):
            return self._process_ibom(file_path, device)
        else:
            result = ImportResult(success=False)
            result.errors.append(f"Unsupported format: {ext}")
            return result

    def _process_pdf(self, file_path, device):
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            result.errors.append("No text extracted from PDF")  # PDF scannerizzato: servira OCR/AI
            return result

        # 1) Parser diretto (gratis)
        entries = parse_pdf_bom_text(text)
        if entries:
            return self._import_entries(entries, device, result)

        # 2) Fallback AI — SOLO se abilitato
        if not self.cfg.deepseek.enabled:
            result.warnings.append("AI extraction is disabled (DEEPSEEK_ENABLED=false)...")
            result.success = False
            return result

        extraction = self._ai.extract_bom(text)
        entries = extraction.entries
        usage = extraction.usage
        result.warnings.append(f"AI extracted {len(entries)} components "
                               f"(tokens: {usage.total_tokens}, est. cost: ${usage.cost_usd:.5f})")
        return self._import_entries(entries, device, result)

    def _import_entries(self, entries, device, result=None) -> ImportResult:
        if result is None:
            result = ImportResult()
        result.total_rows = len(entries)
        device_id = self.db.find_or_create_device(device)
        for entry in entries:
            try:
                self.db.insert_bom_entry(device_id, entry)
                result.imported_rows += 1
            except Exception as e:
                result.failed_rows += 1
                result.errors.append(str(e))
        result.success = result.failed_rows == 0
        return result
```

**Nota:** `_import_entries` ora riceve il risultato di base, così warnings/errors del percorso PDF (es. costo AI) non vengono persi.

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

## pdf_parser.py — Parser Diretto BOM (Regex)

File: `ariadne/pdf_parser.py`

- **Percorso primario** per PDF con testo estraibile — **gratis, nessuna chiamata API**
- `parse_pdf_bom_text(text)` → `list[BOMEntry]`
- Riconosce designator standard (R, C, L, D, U, J, X, Q, SW, LED...) anche multipli sulla stessa riga (`C1,C5,C7`)
- Parsa quantità con moltiplicatore `x` (`2x`) e valori con unità (`100nF`, `4.7k`, `2u2`)
- Rileva **package** da lista ~100+ formati noti (0603, SOT-23, LQFP, QFN, SOIC, THT: DIP/SIP/TO-...)
- Rileva **manufacturer** da lista nota (STM, NXP, TI, Microchip...)
- Deduce **SMT/THT** dal package (DIP/SIP/TO- → THT, altrimenti SMT)
- Gestisce separatori di pagina ("Page N of M") e intestazioni/footer

## ai_client.py — DeepSeek Client (Fallback)

File: `ariadne/ai_client.py`

- Comunica con API DeepSeek (`/v1/chat/completions`, formato OpenAI)
- `extract_bom(text, system_prompt=None)` → `AIExtractionResult(entries, usage)`
- `AIUsage` — token prompt/completion/total + **costo stimato USD** per chiamata
- Log del costo ad ogni chiamata (logger `ariadne.ai`)
- Prezzi stimati configurabili: `INPUT_PRICE_PER_1M` / `OUTPUT_PRICE_PER_1M`
- System prompt specializzato per estrazione BOM
- Parsing robusto: `json.loads()` diretto → fallback blocco ```json
- **Disabilitato di default** (`DEEPSEEK_ENABLED=false`): la key non viene mai usata senza esplicita abilitazione

```python
class DeepSeekClient:
    def __init__(self, config: DeepSeekConfig):
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url

    def extract_bom(self, text: str, system_prompt: str | None = None) -> AIExtractionResult:
        response = self._call_api(text, system_prompt)
        entries = self._parse_response(response)
        usage = self._parse_usage(response)
        return AIExtractionResult(entries=entries, usage=usage)
```

## csv_parser.py — Parsing CSV

File: `ariadne/csv_parser.py`

- Auto-detect delimitatore (virgola o punto e virgola)
- Gestisce formati KiCad (Ref,Qty,Value,Footprint) e EasyEDA (Id,Designator,Package,Quantity)
- `_split_designators()` — separa designator multipli (virgola, punto e virgola o spazio)
- `_detect_mounting_type()` — deduce SMT/THT da footprint e valore
- Gestisce flag DoNotPopulate, Gender, Supplier
- Supporta file `.csv` e `.txt` con lo stesso formato

## ibom_parser.py — Parsing KiCad InteractiveHtmlBom (.html)

File: `ariadne/ibom_parser.py`

- Legge il file `.html`/`.htm` exportato da KiCad **InteractiveHtmlBom** (plugin IBOM)
- Estrae il payload `var pcbdata = JSON.parse(LZString.decompressFromBase64("..."))` tramite regex
- **`lzstring.py`**: decompressore LZ-String base64 puro-Python (senza dipendenze), port fedele dell'algoritmo di riferimento
- Legge `pcbdata.bom.fields` (`{ index: [value, footprint] }`), `pcbdata.bom.both`/`F`/`B` (gruppi di `[ref, value_index]`) e `pcbdata.bom.skipped` (Do-Not-Populate)
- Preferenza **`bom.both`** (tabella BOM completa); se vuoto usa i layer `F`/`B` — evita doppio conteggio quando `both` è popolato e `F`/`B` lo duplicano
- Ogni gruppo diventa un `BOMEntry` (quantity = numero di ref, designator uniti con virgola)
- SMT/THT dedotto dal footprint via `_detect_mounting_type()`

## mdf_ingestor.py + ipc1752.py + mdf_pdf_parser.py — Ingestione MDF (JSON ad-hoc + IPC-1752 Class D + PDF)

File: `ariadne/mdf_ingestor.py`, `ariadne/ipc1752.py`, `ariadne/mdf_pdf_parser.py`

- Obiettivo: estrarre i materiali dai MDF (sia XML IPC-1752 sia PDF di Material Declaration dei produttori) e collegarli alle BOMEntry
- **Percorso JSON (ad-hoc):** `ingest_from_json(path)` — `materials` + `links`, con `device_model` per risolvere i reference; popola `material` + `component_material`
- I link risolvono un reference anche dentro gruppi già uniti con virgola (es. "C1" in "C1,C2") via `Database.find_bom_entry_by_ref()`
- **Percorso XML (standard IPC-1752):** `ingest_from_xml(path)` — legge una **Material Composition Declaration Class D** (IPC-1752A/B, schema ufficiale `http://webstds.ipc.org/175x/2.0`, root `MainDeclaration`)
  - Parser `ariadne/ipc1752.py::parse_class_d_xml()`: namespace-agnostico (match su nomi locali), estrae `Product` → `ProductID@itemNumber`, `HomogeneousMaterial` (`@name`, `@materialGroupName`, `Amount@value/UOM`) → `Substance` (`@name`, `SubstanceID@identity=CAS`, `Amount`, `Concentration@value`)
  - Matching verso la BOM **per part number** (`Database.find_bom_entry_by_part_number()`, normalizzazione maiuscolo/trattini; matcha anche MPN incastonati nel `part_value`, es. `2u2-GRM188R61E225MA12D`)
  - Massa del link: `Amount` assoluto (mg/g/kg → mg) oppure `concentrazione% × massa_materiale_omogeneo`; 0 se non dichiarata
  - Esempio schema-conforme: `test_data/mdf_class_d_sample.xml` (MLCC 2.2uF Murata, 3 materiali omogenei, 7 sostanze con CAS) — al demo linka alle C14/C15 reali di Inkplate 5
- **Percorso PDF:** `ingest_from_pdf(path)` → `parse_pdf_mdf()` (pdfplumber `extract_tables`) riconosce la riga di header sostanze (`Substance Name`/`Substance` + CAS + colonna peso) e produce una lista piatta di `DeclaredSubstance`
  - Layout **ZVEI per-componente**: header a 12 colonne (`Substance Name`, `CAS #`, `Weight [mg]`, `Mass Percent`), massa totale dal metadata (`Mass`/`Unit`); righe con CAS placeholder (`system`, `pseudo substance`, `-`, `Multi`) scartate con warning; righe duplicate della stessa sostanza (nome+CAS) sommato
  - Layout **KEMET/YAGEO per-serie**: colonne `Substance`/`CAS No.` + più colonne `Weight (gr)` (una per variante di taglia) — scelta la prima colonna peso a destra del CAS, grammi → mg
  - Part number candidati estratti dal testo (pattern Murata `GRM...`, KEMET `C…`/`L…`): se trovati in BOM → link; altrimenti **solo materiali** con warning
  - Esempi reali: `test_data/mdf_zvei_mlcc_example.pdf` (MLCC 0603 da 6,3 mg → 4 sostanze) e `test_data/mdf_kemet_c4ak_film.pdf` (serie DC-Link → 15 sostanze)
- `Database.insert_material()` (dedupe per `material_name`), `Database.link_material()` (dedupe per coppia), `Database.get_materials()` (con conteggio `linked_entries`)
- Comando CLI: `ariadne mdf-ingest <file.json|file.xml|file.pdf>` (JSON/XML/PDF → label del percorso nel report, exit 0); il file grezzo viene archiviato in MongoDB (metadata `kind=mdf`) prima del parse
- Comando CLI: `ariadne mdf-download <PART_NUMBER> [--source auto|murata|digikey|mouser|bomcheck|octopart|url:https://...] [--out-dir DIR]` — scarica l'MDF (XML IPC-1752) dai portali pubblici e lo valida col parser

## ods_parser.py — Parsing OpenDocument (.ods)

File: `ariadne/ods_parser.py`

- Legge `.ods` (OpenDocument Spreadsheet) tramite odfpy
- **Schema dinamico**: individua la riga di intestazione per nome colonna (Ref/Qty/Value/Footprint/Description/Manufacturer/Supplier...)
- Gestisce righe di titolo/meta sopra l'header (es. BOM KiCad con header "Title", "Revision", "Date")
- Alias di nomi colonna estesi (Reference, Designator, RefDes, Quantity, Designation, Mfr, MPN, Vendor, MouserPN...)
- Rilevamento SMT/THT da footprint
- `parse_ods_bom(file_path)` → list[BOMEntry]

## eec.py — Classificazione EEC

File: `ariadne/eec.py`

- 16 categorie EEC (Resistors, Capacitors, Inductors, Diodes, Transistors, ICs, Connectors, Switches, Transformers, Fuses, Crystals/Oscillators, LEDs, Sensors, Actuators, Batteries, Other)
- `classify_designator(prefix)` → categoria da singolo designator (R→1, C→2, L→3, D→4, Q→5, U→6, J/CN/K→7, SW→8, T→9, F→10, X/Y→11, LED→12, BT→15)
- `classify_all(designators)` → categoria dominante da stringa multipla (conta e restituisce la più frequente)
- Assegnazione automatica durante l'import (orchestrator)

## export.py — Esportazione Excel

File: `ariadne/export.py`

- `export_device_to_excel(db, device_id, output_path)` → `.xlsx`
- Header formattati (sfondo blu, testo bianco)
- 12 colonne: Item, Qty, Reference, Part Value, Package, Mounting, Manufacturer, Mfr Order Code, Supplier, Supplier Code, EEC Category, Notes
- Larghezze colonne ottimizzate, auto-filter attivo

## mongo_store.py — Archivio Dati Grezzi MongoDB

File: `ariadne/mongo_store.py`

- Archivia i documenti BOM **grezzi** prima dell'elaborazione (Excel→testo, CSV→testo, PDF→testo estratto)
- Collection `bom_files`: `filename`, `file_format`, `content`, `content_hash` (sha256), `metadata`, `created_at`
- `store(filename, file_format, content, metadata)` → ObjectId string o None
- **Optional**: se MongoDB non è raggiungibile, `available=False` e la pipeline continua senza errori (graceful degradation)
- `serverSelectionTimeoutMS=1500` via `_connect()` → fallback rapido
- `_content_hash()` — hash del contenuto per deduplicazione/verifica integrità
- Integrazione: `Orchestrator.process_file()` salva il raw prima del parse; `get_stats()` include `raw_documents` e `raw_available`

## database.py — Wrapper SQLite

File: `ariadne/database.py`

- Usa `sqlite3` (standard library)
- Schema: `device` (id, brand, model_name, manufacturer, year_of_production, notes)
- Schema: `bom_entry` (id, device_id FK, item_number, quantity, reference_designator, part_value, package, manufacturer, manufacturer_order_code, supplier, supplier_order_code, notes, mounting_type, designator_code, eec_category_id)
- `find_or_create_device(device)` → device_id
- `insert_bom_entry(device_id, entry)` → entry_id (None se duplicato: stessa device_id + reference_designator)
- `get_bom_entries(device_id)` → list of rows (per export/verifica)
- `get_stats()` → dict (device, bom_entry, material counts)

## strapi_client.py — Client Strapi REST

File: `ariadne/strapi_client.py`

- Client HTTP per l'headless CMS **Strapi** (REST `/api/...`), usa `httpx`
- Autenticazione **Bearer token** (`Authorization: Bearer <token>`)
- `upsert_device(device)` → cerca per `modelName`, **crea** (POST) o **aggiorna** (PUT); ritorna l'id Strapi
- `push_bom_entry(device, entry, device_strapi_id)` → crea un BOMEntry collegato al device (relazione)
- `sync_device(device, entries)` → upsert device + push di tutte le BOMEntry; ritorna `{device_id, entries_pushed, entry_strapi_ids}` dove `entry_strapi_ids` contiene l'id Strapi di ogni entry **nello stesso ordine** delle entries passate (serve al `strapi-sync --materials` per collegare i materiali alla entry giusta)
- `upsert_material(material)` → upsert per `materialName` univoco (POST/PUT) su `materials`; ritorna l'id Strapi
- `push_component_material(entry_sid, material_sid, mass_mg, note, source_mdf)` → crea il link su `component-materials` (relazioni BOMEntry ↔ Material)
- Campi Strapi in camelCase (`yearOfProduction`, `referenceDesignator`, `eecCategoryId`, `casrn`, `massMg`, `sourceMdf`, ...)
- **Nota**: Strapi usa PostgreSQL (prod) / SQLite (dev); MongoDB resta solo per i dati grezzi

## mdf_portal.py — Downloader MDF dai portali (percorso ONLINE)

File: `ariadne/mdf_portal.py`, CLI: `ariadne mdf-download <PART_NUMBER>`

- I portali (Murata, DigiKey, Mouser, BOMcheck, Octopart) **non espongono un'API documentata** per le Material Declaration → downloader "ad harvest": costruisce le URL di ricerca per il part number, scarica la pagina, estrae i link candidati (pattern tipici: ipc/1752/mcd/material/composition/declaration/rohs/reach + estensione xml/pdf/csv/zip), li ordina per punteggio
- I candidati **XML** vengono scaricati e **validati parseando come IPC-1752 Class D** (`ipc1752.parse_class_d_xml()`); il primo XML valido viene salvato come `<PART>_mdf.xml` in `--out-dir` (default `mdf_downloads`)
- I candidati non-XML (o XML non validi) vengono riportati in `DownloadResult.found`; gli errori di rete in `errors`
- Client HTTP **iniettabile** (`MDFPortalDownloader(client=...)`): i test usano un finto client duck-typed (`.get(url)` → `.text`/`.raise_for_status()`) senza rete
- Source: `auto` (prova tutti i portali in ordine, si ferma al primo MDF valido) | `murata`/`digikey`/`mouser`/`bomcheck`/`octopart` | `url:https://...` (link diretto)
- La **demo resta offline**: questo percorso è opzionale e richiede rete

## web.py — Web UI (Flask)

File: `ariadne/web.py`, template in `ariadne/templates/`

- `create_app(config)` → app Flask che condivide lo stesso DB SQLite della CLI
- Rotta `/` — elenco dispositivi con statistiche
- Rotta `/import` — upload BOM (xlsx/xls/ods/csv/pdf/html) + campi device; redirect al dettaglio del device
- Rotta `/device/<id>` — dettaglio device con componenti e categoria EEC
- Rotta `/device/<id>/export` — download Excel del device
- Rotta `/materials` — pagina Materiali: tabella materiali dichiarati (con conteggio componenti collegati) + tabella link componente→materiale (mass_mg, fonte MDF, note)
- Rotta `/mdf-import` — upload di un MDF (XML IPC-1752 Class D / JSON ad-hoc); popola materiali + link e archivia il file grezzo in MongoDB (metadata `kind=mdf`); redirect a `/materials`
- Nav comune (Home, Import BOM, Import MDF, Materiali) in tutti i template
- Rotta `/api/stats` — statistiche in JSON
- Avvio: `python -m ariadne.web` → http://127.0.0.1:5000
- Nessuna dipendenza da Strapi: la UI lavora sui dati locali; la sincronizzazione è separata

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
# --- DeepSeek AI (fallback a pagamento) ---
# AI DISABILITATA di default. Metti true SOLO quando serve:
# usata come fallback quando il parser diretto non trova nulla.
DEEPSEEK_ENABLED=false
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL=deepseek-chat
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MAX_TOKENS=2000
# STRAPI_BASE_URL=http://localhost:1337
# STRAPI_API_TOKEN=
# SFTP_HOST=
# SFTP_PORT=22
# SFTP_USER=
# SFTP_PASSWORD=
# SFTP_REMOTE_PATH=/uploads
# DATABASE_URL=sqlite:///ariadne.db
# --- MongoDB (dati grezzi, opzionale) ---
# MONGO_URI=mongodb://localhost:27017
# MONGO_DATABASE=ariadne_raw
# MONGO_COLLECTION=bom_files
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
    "pymongo>=4.6",
    "odfpy>=1.4",
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

**186 test, tutti passanti (91% coverage).**

| File | # Test | Cosa verifica |
|------|--------|---------------|
| test_models.py | 5 | BOMEntry, Device, ImportResult |
| test_excel_parser.py | 6 | SMT/THT detection + parse reale |
| test_ods_parser.py | 6 | Parse ODS, THT, meta rows, BOM reale HILTOP |
| test_pdf_parser.py | 10 | Parsing BOM PDF diretto (designator, quantità, package, THT, manufacturer, campione reale) |
| test_pdf_extractor.py | 4 | pdfplumber testo PDF + stream |
| test_ai_client.py | 12 | DeepSeek parsing/cost + mock HTTP |
| test_csv_parser.py | 19 | CSV KiCad/EasyEDA, delimitatori, DNP, reali AMIGA/Inkplate |
| test_ibom_parser.py | 6 | Parse IBOM: gruppi, quantità, preferenza `both`, fallback F/B, DNP, errori |
| test_lzstring.py | 5 | Decompressore LZ-String base64 (vector noti, None/empty, input malformato) |
| test_orchestrator.py | 9 | Flussi Excel/CSV/PDF/ODS/IBOM, AI fallback, duplicati |
| test_new_features.py | 19 | Duplicati, EEC, export Excel |
| test_mongo_store.py | 13 | Raw store offline/online (mock) |
| test_sftp_client.py | 9 | SFTP mock |
| test_cli.py | 12 | CLI end-to-end (process, stats, strapi-sync + --materials, mdf-ingest json/xml/pdf, mdf-download) |
| test_strapi_client.py | 10 | Client Strapi (upsert device/material, push bom-entry/component-material, auth, sync con entry_strapi_ids) |
| test_mdf_ingestor.py | 17 | Ingestione MDF: JSON, IPC-1752 Class D XML (parser/massa/matching part), link query, dedupe, group ref, PDF reale ZVEI, dispatcher |
| test_mdf_pdf_parser.py | 3 | Parser PDF MDF (tabelle sintetiche): layout ZVEI (merge sostanze, intervalli pct), KEMET gr→mg, part number da testo |
| test_mdf_portal.py | 6 | Downloader MDF dai portali: harvest, validazione Class D, candidati non validi, source sconosciuto, stop al primo valido |
| test_web.py | 16 | Web UI (import csv/html, dettaglio, export, stats, /materials, /mdf-import xml+pdf) |

## Risultati reali

| BOM | Formato | Componenti | Import |
|-----|---------|------------|--------|
| STM STEVAL-SPIN3204 | PDF testo | 30 | 30/30 |
| STM STEVAL-SPIN3204 | Excel | 74 | 74/74 |
| Commodore Amiga 2000 | CSV KiCad | 140 | 140/140 |
| e-radionica Inkplate 5 | CSV EasyEDA | 71 | 71/71 |
| Raspberry Pi CM5 IO Board | CSV KiCad | 35 | 35/35 |
| Devtank HILTOP Motherboard | ODS | 160 | 160/160 |
| Oric Remix Issue A (v1.2) | KiCad IBOM (.html) | 127 ref / 76 gruppi | 76/76 |
| **Totale** | | **637** | **586/586** |

**MDF IPC-1752 reale (end-to-end):** `test_data/mdf_class_d_sample.xml` (MLCC Murata 2.2uF `GRM188R61E225MA12D`) → 7 materiali (Barium titanate, Nickel oxide, Lead, Silver, Silicon dioxide, Nickel, Tin) con CAS, linkati alle C14/C15 di Inkplate 5 con massa calcolata da concentrazione × massa del materiale omogeneo.

**MDF PDF reali:** `test_data/mdf_zvei_mlcc_example.pdf` (dichiarazione per-componente ZVEI, MLCC 0603, massa totale 6,3 mg) → 4 sostanze (barium/nickel/copper/tin, massa in mg, part number assente → materials senza link con warning); `test_data/mdf_kemet_c4ak_film.pdf` (dichiarazione di serie KEMET/YAGEO DC-Link, peso in grammi per variante) → 15 sostanze.

## CLI Usage

```bash
ariadne process "BOM.xlsx" --brand STM --model STEVAL-SPIN3204
ariadne process "BOM.ods" --brand Devtank --model "HILTOP Motherboard"
ariadne process "BOM.csv" --brand Commodore --model "Amiga 2000"
ariadne process "BOM.pdf" --brand STM --model STEVAL-SPIN3204   # parser diretto, AI solo se serve
ariadne process "board_ibom.html" --brand Oric --model "Oric Remix Issue A"
ariadne mdf-ingest "test_data/mdf_sample.json"          # MDF ad-hoc (JSON)
ariadne mdf-ingest "test_data/mdf_class_d_sample.xml"    # MDF IPC-1752A/B Class D (XML)
ariadne mdf-ingest "test_data/mdf_zvei_mlcc_example.pdf"  # MDF PDF (layout ZVEI/KEMET, pdfplumber)
ariadne mdf-download GRM188R61E225MA12D --source digikey  # online: scarica l'MDF dal portale
ariadne strapi-sync --materials                          # device+entries+materiali verso Strapi
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
