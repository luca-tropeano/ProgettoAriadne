# Ariadne — BOM Processing Pipeline

**Ariadne Data-Driven Materials Recovery System** — importa, classifica ed esporta Bill of Materials da Excel, CSV e PDF.

## Installazione

```bash
cd src/main/ariadne-py
pip install -e ".[dev]"
```

## Uso

```bash
# Importa BOM Excel
ariadne process "BOM.xlsx" --brand STM --model STEVAL-SPIN3204

# Importa BOM CSV (KiCad, EasyEDA)
ariadne process "BOM.csv" --brand Commodore --model "Amiga 2000"

# Importa BOM PDF (testo estraibile)
ariadne process "BOM.pdf" --brand "Raspberry Pi" --model "CM5 IO Board"

# Mostra statistiche database
ariadne stats
```

## Formati supportati

| Formato | Estensione | Parser | Note |
|---------|-----------|--------|------|
| Excel | `.xlsx` | openpyxl | Header riga 6, 17 colonne |
| CSV KiCad | `.csv` | csv_parser | Separatore `;` o `,`, auto-detect |
| CSV EasyEDA | `.csv` | csv_parser | Separatore `;`, campi quotati |
| PDF testuale | `.pdf` | pdfplumber + pdf_parser | Parser regex diretto, gratis |
| PDF non riconosciuto | `.pdf` | DeepSeek AI | Fallback a pagamento, disabilitato di default |

## Funzionalità

- **Import BOM** da Excel (`.xlsx`), CSV (KiCad/EasyEDA) e PDF testuali
- **Classificazione EEC automatica** — 16 categorie assegnate dai reference designator
- **Controllo duplicati** — skip con warning se la BOM è già stata importata
- **Esportazione Excel** — export del database in `.xlsx` con header formattati
- **Archivio dati grezzi in MongoDB** — ogni file processato viene salvato (contenuto + hash + metadata) prima dell'elaborazione
- **DeepSeek AI fallback** — per PDF non parsabili dal parser diretto (opzionale, a pagamento)
- **Database SQLite locale** — nessun server richiesto per l'uso base
- **54 test pytest** — copertura completa dei parser e della pipeline

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

## Struttura del progetto

```
ariadne-py/
├── ariadne/
│   ├── main.py              # CLI entry point (click)
│   ├── config.py            # Configurazione da .env
│   ├── models.py            # Modelli Pydantic (BOMEntry, Device, Material)
│   ├── database.py          # Wrapper SQLite
│   ├── excel_parser.py      # Parsing Excel (openpyxl)
│   ├── csv_parser.py        # Parsing CSV (KiCad/EasyEDA)
│   ├── pdf_extractor.py     # Estrazione testo PDF (pdfplumber)
│   ├── pdf_parser.py        # Parser diretto BOM (regex, senza AI)
│   ├── ai_client.py         # Client DeepSeek (fallback)
│   ├── orchestrator.py      # Coordinatore pipeline
│   ├── eec.py               # Classificazione EEC 16 categorie
│   ├── export.py            # Export database → Excel
│   ├── mongo_store.py       # Archivio dati grezzi MongoDB (opzionale)
│   └── sftp_client.py       # Upload SFTP (paramiko)
└── tests/
    ├── test_models.py
    ├── test_excel_parser.py
    ├── test_pdf_parser.py
    ├── test_ai_client.py
    ├── test_orchestrator.py
    ├── test_new_features.py
    └── test_mongo_store.py
```

## Test

```bash
cd src/main/ariadne-py
pytest -v
```

**54 test** che coprono:
- Modelli Pydantic (BOMEntry, Device, ImportResult)
- Parser Excel (rilevamento SMT/THT)
- Parser PDF diretto (designator, quantità, package, manufacturer)
- Client DeepSeek (parsing JSON, usage/cost tracking)
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

**Totale: 350 componenti importati, 0 errori.**

## Licenza

Progetto accademico — Università di Genova, Scuola Politecnica, Corso di Ingegneria del Software 80154.
