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

# Mostra statistiche database
ariadne stats

# Avvia l'interfaccia web (http://127.0.0.1:5000)
python -m ariadne.web

# Sincronizza i device verso Strapi (richiede STRAPI_API_TOKEN)
ariadne strapi-sync
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

## Funzionalità

- **Import BOM** da Excel (`.xlsx`), OpenDocument (`.ods`), CSV (KiCad/EasyEDA) e PDF testuali
- **Web UI** — import da browser, visualizzazione componenti con EEC, esportazione Excel, statistiche
- **Sincronizzazione Strapi** — client REST per caricare Device e BOMEntry verso Strapi (PostgreSQL)
- **Classificazione EEC automatica** — 16 categorie assegnate dai reference designator
- **Controllo duplicati** — skip con warning se la BOM è già stata importata
- **Esportazione Excel** — export del database in `.xlsx` con header formattati
- **Archivio dati grezzi in MongoDB** — ogni file processato viene salvato (contenuto + hash + metadata) prima dell'elaborazione
- **DeepSeek AI fallback** — per PDF non parsabili dal parser diretto (opzionale, a pagamento)
- **Database SQLite locale** — nessun server richiesto per l'uso base
- **130 test pytest** — copertura completa dei parser, pipeline, web UI e client Strapi

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
│   ├── pdf_extractor.py     # Estrazione testo PDF (pdfplumber)
│   ├── pdf_parser.py        # Parser diretto BOM (regex, senza AI)
│   ├── ai_client.py         # Client DeepSeek (fallback)
│   ├── orchestrator.py      # Coordinatore pipeline
│   ├── eec.py               # Classificazione EEC 16 categorie
│   ├── export.py            # Export database → Excel
│   ├── mongo_store.py       # Archivio dati grezzi MongoDB (opzionale)
│   ├── strapi_client.py     # Client Strapi REST (Device/BOMEntry sync)
│   └── sftp_client.py       # Upload SFTP (paramiko)
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
    └── test_web.py
```

## Test

```bash
cd src/main/ariadne-py
pytest -v
```

**130 test** che coprono:
- Modelli Pydantic (BOMEntry, Device, ImportResult)
- Parser Excel (rilevamento SMT/THT)
- Parser OpenDocument (.ods)
- Parser PDF diretto (designator, quantità, package, manufacturer)
- Client DeepSeek (parsing JSON, usage/cost tracking)
- Client Strapi (upsert device, push entries, auth Bearer)
- Web UI (import, dettaglio device, export Excel, stats)
- Orchestrator (flussi Excel/CSV/PDF, fallback AI, duplicati)
- Classificazione EEC (16 categorie)
- Esportazione Excel
- Archivio MongoDB raw (online/offline, graceful degradation)

## Risultati reali

| BOM | Formato | Componenti | Import |
|-----|---------|------------|--------|
| STM STEVAL-SPIN3204 | PDF testo | 30 | 30/30 |
| STM STEVAL-SPIN3204 | Excel | 74 | 74/74 |
| Commodore Amiga 2000 | CSV KiCad | 140 | 140/140 |
| e-radionica Inkplate 5 | CSV EasyEDA | 71 | 71/71 |
| Raspberry Pi CM5 IO Board | CSV KiCad | 35 | 35/35 |
| Devtank HILTOP Motherboard | ODS | 160 | 160/160 |

**Totale: 510 componenti importati, 0 errori.**

## Licenza

Progetto accademico — Università di Genova, Scuola Politecnica, Corso di Ingegneria del Software 80154.
