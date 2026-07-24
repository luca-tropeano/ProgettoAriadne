# Guida Implementazione Strapi — Sistema Ariadne (Fase 1)

**VERSIONE: 1.4** | **Data:** 22/07/2026 | **Autore:** Tropeano Luca

## Prerequisiti

- Node.js >= 18
- PostgreSQL >= 14 (sviluppo: SQLite inclusa)
- Strapi >= 5

## Installazione

```bash
npx create-strapi-app@latest ariadne-strapi --quickstart
# oppure con PostgreSQL:
npx create-strapi-app@latest ariadne-strapi --dbclient=postgres --dbhost=localhost --dbport=5432 --dbname=ariadne --dbuser=postgres --dbpassword=...
```

## Creazione Collection Types

### Metodo 1: Tramite Admin UI

Accedere a `/admin` e creare manualmente i Collection Type seguendo la struttura in `../ref/db-structure.md`:

1. Settings → Collection Types → "Create new collection type"
2. Aggiungere i campi con i tipi corrispondenti
3. Configurare le relazioni nella tab "Relations"
4. Settare i permessi in Settings → Users & Permissions Plugin → Roles

### Metodo 2: Tramite Schema JSON (consigliato)

Creare i file schema JSON direttamente nella struttura del progetto. Ogni Collection Type ha un file `schema.json` nella cartella `src/api/<name>/content-types/<name>/`.

Esempio per `eec-category`:

```json
// src/api/eec-category/content-types/eec-category/schema.json
{
  "kind": "collectionType",
  "collectionName": "eec_categories",
  "info": {
    "singularName": "eec-category",
    "pluralName": "eec-categories",
    "displayName": "EEC_Category"
  },
  "options": { "draftAndPublish": false },
  "attributes": {
    "categoryId": { "type": "integer", "required": true, "unique": true, "min": 1, "max": 16 },
    "name": { "type": "string", "required": true },
    "subcategories": { "type": "json" },
    "referenceDesignators": { "type": "relation", "relation": "oneToMany", "target": "api::reference-designator.reference-designator", "mappedBy": "eecCategory" },
    "bomEntries": { "type": "relation", "relation": "oneToMany", "target": "api::bom-entry.bom-entry", "mappedBy": "eecCategory" }
  }
}
```

### Metodo 3: Tramite bootstrap script (seeding + permessi)

Il file `src/index.ts` (TypeScript ESM) gestisce sia il seeding iniziale che la configurazione automatica dei permessi.

**Nota:** Il bootstrap viene eseguito ad ogni avvio di Strapi in sviluppo. Il seeding verifica se i dati esistono già prima di inserirli (idempotente).

```typescript
// src/index.ts
export default {
  async bootstrap({ strapi }: { strapi: any }) {
    // 1. Seed categorie EEC (16 categorie)
    const existingCategories = await strapi.db.query("api::eec-category.eec-category").findMany({});
    if (existingCategories.length === 0) {
      for (const cat of eecCategories) {
        await strapi.entityService.create("api::eec-category.eec-category", { data: cat });
      }
    }

    // 2. Seed reference designator (19 designator)
    const existingDesignators = await strapi.db.query("api::reference-designator.reference-designator").findMany({});
    if (existingDesignators.length === 0) {
      for (const d of designators) {
        await strapi.entityService.create("api::reference-designator.reference-designator", { data: d });
      }
    }

    // 3. Configurazione permessi Public role (CRUD su tutti i Collection Type)
    const publicRole = await strapi.db.query("plugin::users-permissions.role").findOne({ where: { type: "public" } });
    if (publicRole) {
      const apiTypes = [
        "api::eec-category.eec-category",
        "api::reference-designator.reference-designator",
        "api::device.device",
        "api::bom-entry.bom-entry",
        "api::component-material.component-material",
        "api::material.material",
        "api::audit-log.audit-log",
      ];
      const actions = ["find", "findOne", "create", "update", "delete"];

      for (const apiType of apiTypes) {
        for (const action of actions) {
          const existing = await strapi.db.query("plugin::users-permissions.permission").findOne({
            where: { action: `${apiType}.${action}`, role: publicRole.id },
          });
          if (!existing) {
            await strapi.db.query("plugin::users-permissions.permission").create({
              data: { action: `${apiType}.${action}`, role: publicRole.id },
            });
          }
        }
      }
      strapi.log.info("[bootstrap] Public role permissions configured for all API types");
    }
  },
};
```

**Permessi configurati dal bootstrap:**
- `find`, `findOne`, `create`, `update`, `delete` per tutti e 7 i Collection Type
- Ruolo Public (accesso anonimo)
- Le permission vengono create solo se non esistono già (no duplicazioni)

Eseguire con:
```bash
npm run strapi build
npm run develop    # sviluppo con hot-reload
# oppure
npm run start      # produzione
```

## Struttura Directory Consigliata

```
ariadne-strapi/
├── src/
│   ├── index.ts                    # Bootstrap (seeding + permessi)
│   └── api/
│       ├── device/
│       │   ├── content-types/device/schema.json
│       │   ├── controllers/device.ts
│       │   ├── routes/device.ts
│       │   └── services/device.ts
│       ├── bom-entry/
│       │   ├── content-types/bom-entry/schema.json
│       │   ├── controllers/bom-entry.ts
│       │   ├── routes/bom-entry.ts
│       │   └── services/bom-entry.ts
│       ├── component-material/
│       │   └── content-types/component-material/schema.json
│       ├── material/
│       │   └── content-types/material/schema.json
│       ├── reference-designator/
│       │   └── content-types/reference-designator/schema.json
│       ├── eec-category/
│       │   └── content-types/eec-category/schema.json
│       └── audit-log/
│           └── content-types/audit-log/schema.json
├── config/
│   ├── database.ts                 # Configurazione DB (SQLite/PostgreSQL)
│   ├── plugins.ts
│   └── middlewares.ts
├── .tmp/                           # SQLite database (sviluppo)
│   └── data.db
└── package.json
```

## Configurazione Database

### SQLite (sviluppo)

```typescript
// config/database.ts (default da quickstart)
export default ({ env }) => ({
  connection: {
    client: 'sqlite',
    connection: { filename: env('DATABASE_FILENAME', '.tmp/data.db') },
    useNullAsDefault: true,
  },
});
```

### PostgreSQL (produzione)

```typescript
export default ({ env }) => ({
  connection: {
    client: 'postgres',
    connection: {
      host: env('DATABASE_HOST', 'localhost'),
      port: env.int('DATABASE_PORT', 5432),
      database: env('DATABASE_NAME', 'ariadne'),
      user: env('DATABASE_USERNAME', 'postgres'),
      password: env('DATABASE_PASSWORD', ''),
    },
    pool: { min: 2, max: 10 },
  },
});
```

## Configurazione API Key

### Accesso automatico (bootstrap)

Il bootstrap script configura automaticamente i permessi del ruolo Public con CRUD completo su tutti i Collection Type. Nessuna configurazione manuale necessaria per le operazioni di base.

### API Token per import/scrittura

**Nota:** L'API token è opzionale. Il bootstrap configura CRUD completo per il ruolo Public, quindi le operazioni di lettura e scrittura funzionano anche senza token. Lo StrapiClient salta l'header Authorization se il token è vuoto o inizia con `<`.

Per operazioni di import BOM e inserimento dati da servizi esterni (opzionale):

1. Settings → API Tokens → "Create new API Token"
2. Token type: **Custom**
3. Selezionare i permessi: `create`, `update`, `delete` per Device, BOMEntry, ComponentMaterial, Material
4. Copiare il token generato in `appsettings.json` del BOM Import Service

## Verifica Setup

```bash
# Avviare Strapi
npm run develop

# Test health check
curl http://localhost:1337/api/_health

# Test categorie EEC (dovrebbe restituire 16 categorie)
curl http://localhost:1337/api/eec-category

# Test reference designator (dovrebbe restituire 19 designator con populate)
curl "http://localhost:1337/api/reference-designator?populate=eecCategory"

# Test con populate (BOM con materiali)
curl "http://localhost:1337/api/device?populate[bomEntries][populate][componentMaterials][populate][material]=*"

# Test dispositivo specifico
curl "http://localhost:1337/api/device?filters[modelName][$eq]=STEVAL-SPIN3204&populate=*"

# Test BOM entries
curl "http://localhost:1337/api/bom-entry?populate[device]=*&populate[eecCategory]=*"
```

**Note Strapi v5:**
- I percorsi API sono **singolari**: `/api/device` (non `/api/devices`)
- Le relazioni nei payload POST/PUT usano `{ "documentId": "xxx" }` (non ID interi)
- `populate=<field>` per includere relazioni nelle risposte GET

## Accesso ai Dati

```bash
# Accesso senza token (Public role con CRUD completo)
curl http://localhost:1337/api/device

# API Key authentication (opzionale, per import/scrittura)
curl -H "Authorization: Bearer <api-token>" http://localhost:1337/api/device

# Popolare relazioni per query "quali/quanti/dove"
curl "http://localhost:1337/api/device?populate[bomEntries][populate][componentMaterials][populate][material]=*"

# Filtrare per modello specifico
curl "http://localhost:1337/api/device?filters[modelName][$eq]=STEVAL-SPIN3204&populate=*"

# Inserire un BOMEntry (relations via documentId)
curl -X POST http://localhost:1337/api/bom-entry \
  -H "Content-Type: application/json" \
  -d '{"data": {"itemNumber": 1, "quantity": 14, "referenceDesignator": "C1,C5", "mountingType": "SMT", "device": {"documentId": "xyz123"}, "eecCategory": {"documentId": "abc456"}}}'
```
