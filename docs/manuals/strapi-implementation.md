# Guida Implementazione Strapi — Sistema Ariadne (Fase 1)

## Prerequisiti

- Node.js >= 18
- PostgreSQL >= 14
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

### Metodo 2: Tramite bootstrap script

Creare il file `src/index.js` nello strapi project con il seeding automatico:

```javascript
module.exports = {
  async bootstrap({ strapi }) {
    // Crea categorie EEC
    const eecCategories = [
      { categoryId: 1, name: "Cable Assemblies", subcategories: ["Data Transmission", "Fiber Optic", "RF-Microwave Assemblies"] },
      { categoryId: 2, name: "Capacitors", subcategories: ["Aluminum Solid", "Ceramic", "Film", "Glass", "Mica", "Semiconductor", "Tantalum"] },
      // ... tutte le 16 categorie
    ];
    for (const cat of eecCategories) {
      await strapi.entityService.create('api::eec-category.eec-category', { data: cat });
    }

    // Crea reference designator
    const designators = [
      { designatorCode: "R", name: "Resistor", description: "Resistore", eecCategory: 12 },
      { designatorCode: "C", name: "Capacitor", description: "Condensatore", eecCategory: 2 },
      // ... tutti i designator
    ];
    for (const d of designators) {
      await strapi.entityService.create('api::reference-designator.reference-designator', { data: d });
    }
  },
};
```

Eseguire con:
```bash
npm run strapi build
npm run develop
```

## Configurazione API Key

1. Settings → Users & Permissions Plugin → Roles → Public
   - Abilitare `find` e `findOne` per i Collection Type in lettura
2. Settings → Users & Permissions Plugin → Roles → Authenticated
   - Creare un API Token con permessi di scrittura
3. Settings → API Tokens → "Create new API Token"
   - Selezionare i permessi: create/update per Device, BOMEntry, ComponentMaterial, Material

## Verifica setup

```bash
# Test connessione
curl http://localhost:1337/api/_health

# Lista categorie EEC
curl http://localhost:1337/api/eec-categories

# Lista designator
curl http://localhost:1337/api/reference-designators
```

## Accesso ai dati

```bash
# API Key authentication
curl -H "Authorization: Bearer <api-token>" http://localhost:1337/api/devices

# Populate relazioni per query "quali/quanti/dove"
curl "http://localhost:1337/api/devices?populate[bomEntries][populate][componentMaterials][populate][material]=*"
```
