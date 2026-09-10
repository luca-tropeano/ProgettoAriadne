# Ariadne — BOM Processing Pipeline

**Ariadne Data-Driven Materials Recovery System** — importa, classifica ed esporta Bill of Materials da Excel, CSV e PDF. Include interfaccia web e sincronizzazione verso Strapi.

## Installazione

```bash
cd src/main/ariadne-py
pip install -e ".[dev]"
```

## Uso

```bash
# Importa BOM Excel
ariadne process "BOM.xlsx" --brand STM --model STEVAL-SPIN3204

# Importa BOM OpenDocument (.ods)
ariadne process "BOM.ods" --brand Devtank --model "HILTOP Motherboard"

# Importa BOM CSV (KiCad, EasyEDA)
ariadne process "BOM.csv" --brand Commodore --model "Amiga 2000"

# Importa BOM PDF (testo estraibile)
ariadne process "BOM.pdf" --brand "Raspberry Pi" --model "CM5 IO Board"

# Importa BOM KiCad InteractiveHtmlBom (.html)
ariadne process "board_ibom.html" --brand Oric --model "Oric Remix Issue A"

# Importa BOM Markdown (.md, tabelle GFM: Ref/Value/Qty/Footprint/Manufacturer/MPN)
ariadne process "BOM.md" --brand Commodore --model "Amiga 2000"

# Sourcing MDF AUTOMATICO all'import (MDF_AUTO=true di default):
#   - componenti coperti da una family MCD (KEMET/YAGEO MLCC → MCD-Ceramic.pdf)
#     → materiali linkati alle BOMEntry del device durante il process;
#   - componenti con part number ma senza MCD → annota la BOMEntry (notes)
#     con la pagina ufficiale di conformità del produttore;
#   - componenti generici/DNF senza MPN → nessuna fonte ricercabile.
# Per disabilitare: ariadne process BOM.xlsx ... (--no-auto-mdf) oppure MDF_AUTO=false

# Ingestione materiali da MDF (pipeline manuale, formati aggiuntivi)
#   JSON ad-hoc (formato documentato in ariadne/mdf_ingestor.py)
ariadne mdf-ingest "test_data/mdf_sample.json"
#   XML IPC-1752A/B Class D (Material Composition Declaration)
#   → le sostanze dichiarate diventano material e vengono linkate alla BOM
ariadne mdf-ingest "test_data/mdf_class_d_sample.xml"
#   PDF Material Declaration (layout ZVEI per-componente / KEMET/YAGEO per-serie):
#   → le sostanze dichiarate (nome + CAS + massa) diventano material;
#     il link alla BOM avviene solo se nel PDF compare un part number riconosciuto
ariadne mdf-ingest "test_data/mdf_zvei_mlcc_example.pdf"

# Download dell'MDF dai portali pubblici (ONLINE, opzionale):
#   prova a scaricare la Material Composition Declaration (XML IPC-1752)
#   del produttore/distributore e la valida col parser Class D
ariadne mdf-download GRM188R61E225MA12D --source digikey

# Mostra statistiche database
ariadne stats

# Avvia l'interfaccia web (http://127.0.0.1:5000)
python -m ariadne.web

# Sincronizza i device verso Strapi (richiede STRAPI_API_TOKEN)
ariadne strapi-sync
# Sincronizza anche i materiali MDF (materials + component-materials) verso Strapi
ariadne strapi-sync --materials
```

**Censimento componenti e MDF finder (report per-componente):**

```bash
# Elenca tutti i gruppi di componenti dei DB (demo.db + ariadne.db)
python scripts/census_components.py                  # → mdf_prospecting/census_*.json
# Report per-componente della fonte MDF (family_mcd / reference / no_mpn)
python scripts/mdf_finder.py                         # → mdf_prospecting/mdf_report.csv|.json
# Genera gli MDF JSON per-famiglia MLCC dai dati di test_data/mdf/MCD-Ceramic.pdf
python scripts/generate_family_mdf_json.py           # → test_data/mdf/MDF_MCD_MLCC_*.json
```

**Demo (presentazione):** avvia Web UI con 2 BOM reali già importate (231 componenti), materiali MDF (JSON campione + dichiarazione IPC-1752 Class D + **PDF Material Declaration ZVEI** + **MCD famiglia MLCC KEMET/YAGEO**) e (se presente) l'IBOM KiCad di Oric

```bash
powershell -ExecutionPolicy Bypass -File run_demo.ps1
```

## Formati supportati

| Formato | Estensione | Parser | Note |
|---------|-----------|--------|------|
| Excel | `.xlsx` | openpyxl | Header riga 6, 17 colonne |
| OpenDocument | `.ods` | ods_parser | Schema dinamico, header per nome colonna |
| CSV KiCad | `.csv` | csv_parser | Separatore `;` o `,`, auto-detect |
| CSV EasyEDA | `.csv` | csv_parser | Separatore `;`, campi quotati |
| PDF testuale | `.pdf` | pdfplumber + pdf_parser | Parser regex diretto, gratis |
| PDF non riconosciuto | `.pdf` | DeepSeek AI | Fallback a pagamento, disabilitato di default |
| InteractiveHtmlBom | `.html`/`.htm` | ibom_parser | KiCad IBOM (payload `pcbdata` LZ-String) |
| Markdown | `.md`/`.markdown` | md_parser | Tabelle GFM (`Ref`/`Value`/`Qty`/`Footprint`/`Manufacturer`/`MPN`), qty opzionale |

## Funzionalità

- **Import BOM** da Excel (`.xlsx`), OpenDocument (`.ods`), CSV (KiCad/EasyEDA), PDF testuali, KiCad InteractiveHtmlBom (`.html`) e **Markdown (`.md`, tabelle GFM)**
- **Web UI** — import da browser, visualizzazione componenti con EEC, esportazione Excel, statistiche, **pagina Materiali** e **import MDF** (upload XML IPC-1752 / JSON / PDF)
- **Sincronizzazione Strapi** — client REST per caricare Device, BOMEntry e (con `--materials`) Materiali/ComponentMaterial verso Strapi (PostgreSQL)
- **Classificazione EEC automatica** — 16 categorie assegnate dai reference designator
- **Ingestione MDF** — comando `mdf-ingest`: JSON ad-hoc, **XML IPC-1752A/B Class D** e **PDF Material Declaration** (pdfplumber, layout ZVEI/KEMET) popolano `material` + `component_material` (matching per part number, massa da concentrazione/peso dichiarato)
- **Sourcing MDF automatico all'import** — allineato a `MDF_AUTO` (default `true`): dopo ogni process, `ariadne/mdf_auto.py` classifica i componenti con `ariadne/mdf_rules.py` e ingerisce family MCD (link `material`↔`component_material`) o annota le BOMEntry con il link di conformità del produttore nella colonna `notes`; idempotente (dedup su `material` e `component_material`), mai bloccante per l'import
- **MDF per-famiglia (real)** — `test_data/mdf/` contiene le Material Composition Declaration YAGEO (ceramic MLCC, tantalum, film EMI/RFI) scaricate da `yageogroup.com`; `scripts/generate_family_mdf_json.py` rigenera gli MDF JSON per-famiglia (per audit/manutenzione) e `ariadne.mdf_auto` li applica automaticamente alle BOMEntry KEMET/YAGEO
- **MDF finder** — `scripts/mdf_finder.py` produce il report per-componente della fonte MDF (`family_mcd` / `reference` / `no_mpn`) con il link ufficiale di conformità per produttore (stesse regole del sourcing automatico, in `ariadne/mdf_rules.py`)
- **Downloader MDF (online, opzionale)** — comando `mdf-download`: ricerca dell'MDF sui portali pubblici (Murata/DigiKey/Mouser/BOMcheck/Octopart/URL diretto), estrae i candidati e li valida col parser IPC-1752
- **Controllo duplicati** — skip con warning se la BOM è già stata importata
- **Esportazione Excel** — export del database in `.xlsx` con header formattati
- **Archivio dati grezzi in MongoDB** — ogni file processato (BOM e MDF) viene salvato (contenuto + hash + metadata) prima dell'elaborazione
- **DeepSeek AI fallback** — per PDF non parsabili dal parser diretto (opzionale, a pagamento)
- **Database SQLite locale** — nessun server richiesto per l'uso base
- **Web UI completa** — restyle condiviso (style.css), ricerca live su device e materiali, modifica device e componenti, recap differenze al re-import di un prodotto già presente, link rivenditori
- **245 test pytest** — copertura completa dei parser, pipeline, web UI (import, edit, recap, materiali), IBOM, MDF, sourcing auto e client Strapi

## Configurazione

Copia `.env.example` in `.env` e compila:

```bash
cp .env.example .env
```

Variabili d'ambiente principali:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DEEPSEEK_ENABLED` | `false` | Abilita il fallback AI (a pagamento) |
| `DEEPSEEK_API_KEY` | — | Chiave API DeepSeek |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Modello DeepSeek |
| `DEEPSEEK_MAX_TOKENS` | `2000` | Token massimi per chiamata |
| `DATABASE_URL` | `sqlite:///ariadne.db` | URL database |
| `MDF_AUTO` | `true` | Sourcing MDF automatico all'import BOM (`ariadne/mdf_auto.py`): family MCD linkate + annotazione riferimenti conformità; `false` o flag CLI `--no-auto-mdf` per disabilitarlo |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB (dati grezzi, opzionale) |
| `MONGO_DATABASE` | `ariadne_raw` | Database MongoDB |
| `MONGO_COLLECTION` | `bom_files` | Collection raw documents |
| `STRAPI_BASE_URL` | `http://localhost:1337` | URL istanza Strapi |
| `STRAPI_API_TOKEN` | — | Token API Strapi (per `strapi-sync`) |

## Struttura del progetto

```
ariadne-py/
├── ariadne/
│   ├── main.py              # CLI entry point (click)
│   ├── web.py               # Web UI (Flask)
│   ├── templates/           # Template HTML della Web UI
│   ├── config.py            # Configurazione da .env
│   ├── models.py            # Modelli Pydantic (BOMEntry, Device, Material)
│   ├── database.py          # Wrapper SQLite
│   ├── excel_parser.py      # Parsing Excel (openpyxl)
│   ├── ods_parser.py        # Parsing OpenDocument (.ods)
│   ├── csv_parser.py        # Parsing CSV (KiCad/EasyEDA)
│   ├── md_parser.py         # Parsing Markdown (tabelle GFM)
│   ├── pdf_extractor.py     # Estrazione testo PDF (pdfplumber)
│   ├── pdf_parser.py        # Parser diretto BOM (regex, senza AI)
│   ├── ai_client.py         # Client DeepSeek (fallback)
│   ├── ibom_parser.py        # Parsing KiCad InteractiveHtmlBom (pcbdata)
│   ├── lzstring.py            # Decompressione LZ-String (payload IBOM)
│   ├── mdf_ingestor.py        # Ingestione MDF (JSON ad-hoc + XML IPC-1752 + PDF)
│   ├── mdf_pdf_parser.py      # Parser Material Declaration PDF (pdfplumber, ZVEI/KEMET)
│   ├── mdf_rules.py           # Regole sourcing MDF per-componente (family MCD / reference / no_mpn)
│   ├── mdf_auto.py            # Sourcing MDF automatico all'import BOM
│   ├── ipc1752.py             # Parser IPC-1752A/B Class D (XML)
│   ├── mdf_portal.py          # Downloader MDF dai portali (harvest + validazione)
│   ├── orchestrator.py      # Coordinatore pipeline
│   ├── eec.py               # Classificazione EEC 16 categorie
│   ├── export.py            # Export database → Excel
│   ├── mongo_store.py       # Archivio dati grezzi MongoDB (opzionale)
│   ├── strapi_client.py     # Client Strapi REST (Device/BOMEntry/Material sync)
│   └── sftp_client.py       # Upload SFTP (paramiko)
├── scripts/
│   ├── census_components.py          # Censimento componenti (demo.db + ariadne.db)
│   ├── mdf_finder.py                 # Report per-componente fonte MDF
│   └── generate_family_mdf_json.py   # MDF JSON per-famiglia MLCC da MCD-Ceramic.pdf
├── mdf_prospecting/                  # Census + report MDF (output degli script)
├── test_data/
│   ├── mdf/                          # MDF reali per-famiglia (MCD-Ceramic/Tantalum/Film)
│   └── ...                           # fixture BOM (PDF/Excel/CSV/ODS/HTML)
└── tests/
    ├── test_models.py
    ├── test_excel_parser.py
    ├── test_ods_parser.py
    ├── test_pdf_parser.py
    ├── test_ai_client.py
    ├── test_orchestrator.py
    ├── test_new_features.py
    ├── test_mongo_store.py
    ├── test_strapi_client.py
    ├── test_lzstring.py
    ├── test_ibom_parser.py
    ├── test_mdf_ingestor.py
    ├── test_mdf_pdf_parser.py
    ├── test_mdf_portal.py
    └── test_web.py
```

## Test

```bash
cd src/main/ariadne-py
pytest -v
```

**187 test, 91% coverage** che coprono:
- Modelli Pydantic (BOMEntry, Device, ImportResult)
- Parser Excel (rilevamento SMT/THT)
- Parser OpenDocument (.ods)
- Parser PDF diretto (designator, quantità, package, manufacturer)
- Client DeepSeek (parsing JSON, usage/cost tracking)
- Client Strapi (upsert device/material, push entries/component-material, auth Bearer)
- Web UI (import, dettaglio device, export Excel, stats, Materiali, import MDF)
- Orchestrator (flussi Excel/CSV/PDF, fallback AI, duplicati, ingest MDF + archivio raw)
- Classificazione EEC (16 categorie)
- Esportazione Excel
- Archivio MongoDB raw (online/offline, graceful degradation)
- IBOM KiCad (LZ-String + parser `pcbdata`)
- Ingestione MDF (JSON ad-hoc, IPC-1752 Class D XML, link query, CLI)
- Parser PDF MDF (pdfplumber: layout ZVEI per-componente e KEMET/YAGEO per-serie, mg/gr)
- Downloader MDF dai portali (harvest, validazione Class D, client mock)

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

**Totale: 586 componenti importati, 0 errori.**

**MDF IPC-1752 reale (end-to-end):** `test_data/mdf_class_d_sample.xml` (MLCC Murata 2.2uF `GRM188R61E225MA12D`) → 7 materiali con CAS linkati alle C14/C15 di Inkplate 5.

**MDF PDF reali:** `test_data/mdf_zvei_mlcc_example.pdf` (dichiarazione per-componente ZVEI, MLCC 0603, massa 6,3 mg) → 4 sostanze (barium/nickel/copper/tin, CAS e peso in mg, senza part number → warning); `test_data/mdf_kemet_c4ak_film.pdf` (dichiarazione di serie KEMET/YAGEO DC-Link, peso in gr → 15 sostanze).

**Sourcing MDF automatico (MDF_AUTO=true):** all'import di una BOM, `ariadne/mdf_auto.py` classifica i componenti con `ariadne/mdf_rules.py`; quelli coperti da family MCD (KEMET/YAGEO MLCC) vengono linkati automaticamente alle BOMEntry, gli altri con MPN vengono annotati (colonna `notes`) con la pagina ufficiale di conformità del produttore, i generici/DNF vengono ignorati. Sul HILTOP: 6 gruppi KEMET/YAGEO → 36 link materials (6 sostanze × 6 BOMEntry) + 104 riferimenti conformità annotati; 1 gruppo senza MPN. Pipeline idempotente (dedup per `bom_entry_id`+`material_id`) e non bloccante.

**MDF reali per-famiglia (YAGEO Group, scaricati da yageogroup.com):** `test_data/mdf/MCD-Ceramic.pdf` (Material Composition Declaration MLCC X7R/X5R/C0G, giugno 2026), `MCD-Tantalum.pdf`, `MCD-Film-EMI-RFI-Suppression-March-2022.pdf`. La famiglia ceramica è stata ingerita e linkata ai componenti KEMET/YAGEO reali:

| DB | BOM entries linkate | materiali | source |
|----|--------------------|-----------|--------|
| `demo.db` (HILTOP) | 6 | BaTiO3, Ni, Cu, Sn, Ag, CaZrO3 | `MCD-Ceramic.pdf` |
| `ariadne.db` (STEVAL-SPIN3204) | 38 | BaTiO3, Ni, Cu, Sn, Ag, CaZrO3 | `MCD-Ceramic.pdf` |

**MDF finder (381 componenti su due DB):** 17 gruppi coperti da family MCD (`family_mcd`), 163 con link ufficiale di conformità del produttore (`reference`), 201 senza part number ricercabile (`no_mpn`). Report: `mdf_prospecting/mdf_report.csv` (o `.json`).

## Licenza

Progetto accademico — Università di Genova, Scuola Politecnica, Corso di Ingegneria del Software 80154.
