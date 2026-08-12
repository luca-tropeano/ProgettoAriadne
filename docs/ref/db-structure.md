# Struttura del Database — Sistema Ariadne di Recupero Materiali (Fase 1)

**VERSIONE : 1.5** | **Data:** 29/07/2026 | **Autore:** Tropeano Luca

## Piattaforma

Database gestito tramite **Strapi** (headless CMS) oppure **SQLite locale** (Python pipeline). L'accesso avviene tramite **API REST** di Strapi (quando configurato) o direttamente via SQLite (modalità locale).

I file Excel (.xlsx) sono usati solo come **formato di input** per l'importazione BOM e opzionalmente per la verifica intermedia dei dati MDF.

Il database risponde a: **QUALI** materiali, **QUANTI** (massa), e **DOVE** (quale componente) si trovano in un dispositivo (Punto C1 del flusso dati Ariadne).

**Nota sul "DOVE":** A livello di componente C1, "dove" indica **in quale componente** (quale riga di BOM, identificata dal reference designator), non la posizione interna al componente. Per quanto alcune MDF riportino la distribuzione interna dei materiali (es. incapsulamento, terminali, die), questa distinzione non è tecnicamente rilevante ai fini del recupero. Per ciascun elemento/materiale, il sistema memorizza la massa totale per ogni singolo componente.

---

## Collection Types Strapi

Ogni tabella è un **Collection Type** Strapi. Le relazioni sono nativamente gestite da Strapi tramite campi "relation". Le API CRUD sono generate automaticamente.

### 1. Device

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| brand | Text | required, minLength(1) | Marca del dispositivo | STMicroelectronics |
| modelName | Text | required, unique | Nome modello (univoco) | STEVAL-SPIN3204 |
| manufacturer | Text | required | Nome del produttore | STMICROELECTRONICS |
| yearOfProduction | Integer | required, min(1900), max(2030) | Anno di produzione | 2021 |
| notes | RichText | optional | Note aggiuntive | Rev 211 |

**Relazioni:**
- `bomEntries` — Relation `oneToMany` → BOMEntry
- `auditLogs` — Relation `oneToMany` → AuditLog

**Permessi:** CRUD Admin/API Key; lettura Public.

### 2. BOMEntry

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| itemNumber | Integer | required | Numero riga nella BOM | 1 |
| quantity | Integer | required, min(1) | Quantità del componente | 14 |
| referenceDesignator | Text | required | Designator (separati da virgola) | C1,C5,C7,C8,C9,C11,C20... |
| mountingType | Enumeration | required, enum: SMT, THT | Tipo montaggio | SMT |
| partValue | Text | optional | Valore del componente | 100 nF |
| manufacturer | Text | optional | Produttore del componente | KEMET |
| manufacturerOrderCode | Text | optional | Codice ordinamento produttore | C0603C104K5RACTU |
| supplier1 | Text | optional | Primo fornitore | DIGIKEY |
| supplier1OrderCode | Text | optional | Catalogo fornitore 1 | PCE3820CT-ND |
| supplier2 | Text | optional | Secondo fornitore | MOUSER |
| supplier2OrderCode | Text | optional | Catalogo fornitore 2 | 12345 |
| supplier3 | Text | optional | Terzo fornitore | FARNELL |
| supplier3OrderCode | Text | optional | Catalogo fornitore 3 | 67890 |
| designatorCode | Text | optional | Codice designator (R, C, U...) | C |
| notes | RichText | optional | Note aggiuntive | Appro ADEX |

**Relazioni:**
- `device` — Relation `manyToOne` → Device (required)
- `eecCategory` — Relation `manyToOne` → EEC_Category (required)
- `componentMaterials` — Relation `oneToMany` → ComponentMaterial

**Permessi:** create/update via API Key (import BOM), lettura Public.

### 3. ComponentMaterial

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| massMg | Decimal | required, min(0) | Massa in mg | 12.5000 |
| note | Text | optional | Nota (lega, CASRN alternativo) | Wire termination |
| sourceMdf | Text | optional | Nome file MDF di origine | MDF_KEMET_C0603.pdf |

**Relazioni:**
- `bomEntry` — Relation `manyToOne` → BOMEntry (required)
- `material` — Relation `manyToOne` → Material (required)

**Permessi:** create/update via API Key (inserimento MDF), lettura Public.

### 4. Material

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| materialName | Text | required, unique | Nome materiale (sempre in inglese) | Copper |
| casrn | Text | optional, unique, regex: ^\d{2,7}-\d{2}-\d$ | CAS Registry Number (formato xxx-yy-z) | 7440-50-8 |
| category | Enumeration | required, enum: element, compound | Classificazione | element |

**Relazioni:**
- `componentMaterials` — Relation `oneToMany` → ComponentMaterial

**Permessi:** create/update via API Key, lettura Public.

### 5. ReferenceDesignator

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| designatorCode | UID | required, unique | Codice designator (univoco) | R |
| name | Text | required | Nome tipo componente | Resistor |
| description | Text | optional | Descrizione completa | Resistenza |

**Relazioni:**
- `eecCategory` — Relation `manyToOne` → EEC_Category (required)

### 6. EEC_Category

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| categoryId | Integer | required, unique, min(1), max(16) | Numero categoria (1-16) | 12 |
| name | Text | required | Nome categoria | Resistors |
| subcategories | JSON | optional | Lista JSON sottocategorie | ["Film","Metal Foil","Network Arrays"] |

**Relazioni:**
- `referenceDesignators` — Relation `oneToMany` → ReferenceDesignator
- `bomEntries` — Relation `oneToMany` → BOMEntry

### 7. AuditLog

| Campo | Tipo Strapi | Vincoli/Validazione | Descrizione | Esempio |
|-------|------------|-------------------|-------------|---------|
| timestamp | DateTime | required | Data/ora evento | 2026-06-28T10:30:00Z |
| userId | Text | required | Identificativo utente | luca.tropeano |
| action | Text | required | Azione eseguita | BOM_IMPORT |
| details | RichText | optional | Dettagli aggiuntivi | 74 componenti importati |

**Relazioni:**
- `device` — Relation `manyToOne` → Device (required)

**Permessi:** sola scrittura da backend, lettura Admin.

---

### Riepilogo Permessi

| Ruolo | Collection Types accessibili | Operazioni |
|-------|---------------------------|------------|
| Public API (anonimo) | Device, BOMEntry, ComponentMaterial, Material, ReferenceDesignator, EEC_Category, AuditLog | CRUD completo (tutte le operazioni) |
| API Key (import BOM) | Device, BOMEntry, ComponentMaterial, Material, EEC_Category | POST, PUT (import dati) |
| Admin (Strapi admin UI) | Tutti | CRUD completo, gestione permessi |

**Nota:** I permessi del ruolo Public vengono configurati automaticamente dal bootstrap script (`src/index.ts`) ad ogni avvio di Strapi in sviluppo. Il bootstrap crea permessi `find`, `findOne`, `create`, `update`, `delete` per tutti e 7 i Collection Type, verificando che non esistano già per evitare duplicazioni. L'API token è opzionale — quando vuoto o inizia con `<`, lo StrapiClient salta l'header Authorization e si affida ai permessi CRUD del ruolo Public.

---

## API Endpoint Strapi

Tutti i dati sono accessibili tramite API REST generate da Strapi:

### Esempi di chiamata API

```http
# Quali materiali sono in un dispositivo (fetch Device con populate)
GET /api/device?populate[bomEntries][populate][componentMaterials][populate][material]=*

# Quanto (massa) di ogni materiale?
GET /api/device?filters[modelName][$eq]=STEVAL-SPIN3204&populate[bomEntries][populate][componentMaterials][populate][material]=*

# Dove (quale componente) si trova un materiale specifico?
GET /api/component-material?filters[material][casrn][$eq]=7440-50-8&populate[bomEntry]=*

# Inserimento di un nuovo Device
POST /api/device
{
  "data": {
    "brand": "STMicroelectronics",
    "modelName": "STEVAL-SPIN3204",
    "manufacturer": "STMICROELECTRONICS",
    "yearOfProduction": 2021
  }
}

# Inserimento di un BOMEntry collegato a un Device (Strapi v5: relations via documentId)
POST /api/bom-entry
{
  "data": {
    "itemNumber": 1,
    "quantity": 14,
    "referenceDesignator": "C1,C5,C7,C8,C9,C11,C20...",
    "mountingType": "SMT",
    "partValue": "100 nF",
    "manufacturer": "KEMET",
    "manufacturerOrderCode": "C0603C104K5RACTU",
    "device": { "documentId": "xyz123" },
    "eecCategory": { "documentId": "abc456" }
  }
}

# Inserimento dati materiali da MDF (relations via documentId)
POST /api/component-material
{
  "data": {
    "massMg": 12.5,
    "note": "Wire termination",
    "sourceMdf": "MDF_KEMET_C0603.pdf",
    "bomEntry": { "documentId": "bom123" },
    "material": { "documentId": "mat456" }
  }
}
```

**Nota Strapi v5:** I percorsi API sono **singolari** (`/api/device`, non `/api/devices`). Le relazioni nei payload POST/PUT devono usare il formato `{ "documentId": "xxx" }` — gli ID interi grezzi causano errori 400.

---

## Pipeline Dati MDF

```
┌──────────┐    ┌──────────────┐    ┌──────────────────────┐
│ BOM Excel│───▶│ openpyxl     │───▶│ SQLite / Strapi      │
│ (.xlsx)  │    │ Parser       │    │ → Collection Type     │
└──────────┘    └──────────────┘    └────────┬─────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                         ┌──────────│  BOM PDF (input)  │
                         │          └────────┬─────────┘
                         ▼                   ▼
               ┌─────────────────┐  ┌──────────────────┐
               │ Inserimento     │  │ pdfplumber        │
               │ Manuale (via UI)│  │ (text extraction)  │
               └────────┬────────┘  └────────┬─────────┘
                        │                    ▼
                        │          ┌──────────────────────┐
                        │          │ pdf_parser           │
                        │          │ (parser diretto,     │
                        │          │  regex, senza AI)    │
                        │          └──────────┬───────────┘
                        │                     ▼
                        │          ┌──────────────────────┐
                        │          │ 0 entries e          │
                        │          │ DEEPSEEK_ENABLED=true?│
                        │          └──────────┬───────────┘
                        │              no     ▼      sì
                        │          ┌──────────────────────┐
                        │          │ DeepSeek AI API       │
                        │          │ (fallback a pagamento)│
                        │          └──────────┬───────────┘
                        │                     ▼
                        │          ┌──────────────────────┐
                        │          │ JSON → BOMEntry       │
                        │          │ (validazione Pydantic)│
                        │          └──────────┬───────────┘
                        ▼                     ▼
               ┌──────────────────────────────────────────┐
               │       SQLite (locale) / Strapi API        │
               │  (INSERT → device + bom_entry tables)     │
               └──────────────────────────────────────────┘
                        │
                        ▼
               ┌──────────────────────────────────────────┐
               │       SQLite DB / PostgreSQL              │
               │  (query "quali/quanti/dove")              │
               └──────────────────────────────────────────┘
```

**Flussi implementati:**
1. **Excel → DB** (BOM Import): `Orchestrator._process_excel()` → `parse_excel_bom()` (openpyxl) → `Database.insert_bom_entry()`
2. **PDF → parser diretto → DB** (percorso primario, gratis): `extract_text_from_pdf()` (pdfplumber) + `parse_pdf_bom_text()` (regex) → `Orchestrator._import_entries()` → SQLite
3. **PDF → DeepSeek AI → DB** (fallback a pagamento, disabilitato di default): usato solo se il parser diretto trova 0 entries e `DEEPSEEK_ENABLED=true`. Costo/token loggati ad ogni chiamata
4. **Inserimento manuale** (via Admin UI o API): accesso diretto ai Collection Type Strapi (se configurato)
5. **Export database → Excel**: export tool tramite openpyxl — dati da SQLite/Strapi API

**Note implementative:**
- **EECClassifier**: query al database locale o Strapi API per mapping designator → categoria EEC
- **Database**: wrapper SQLite con connessione diretta (nessuna serializzazione JSON necessaria per operazioni locali)
- **Strapi (opzionale)**: se configurato, i dati possono essere sincronizzati con Strapi API tramite variabili d'ambiente (`.env`)
