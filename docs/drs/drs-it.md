# Sistema Ariadne di Recupero Materiali Data-Driven

## Documento di Specifica dei Requisiti di Progetto

DIBRIS – Università di Genova. Scuola Politecnica, Corso di Ingegneria del Software 80154

<div align='right'> <b> Autori </b> <br> Tropeano Luca </div>

**VERSIONE : 1.9**

### STORIO REVISIONI

| Versione | Data       | Autore(i) | Note                                                                                                               |
| -------- | ---------- | --------- | ------------------------------------------------------------------------------------------------------------------ |
| 1.0      | 27/06/2026 | Tropeano  | Prima versione completa basata sui dati di progetto                                                                |
| 1.1      | 28/06/2026 | Tropeano  | Revisione dopo feedback Rosario — scope focalizzato su soli C1, schema DB semplificato, rimossi moduli fasi future |
| 1.2      | 02/07/2026 | Tropeano  | Revisione feedback Rosario v2: MountingType, SMT/THT, 'dove' chiarito, EEC≠designator spiegato, allineamento URS/DRS |
| 1.3      | 02/07/2026 | Tropeano  | Integrazione Strapi: sostituito SQL Server diretto con Strapi headless CMS + PostgreSQL, aggiornato stack tecnologico e architettura |
| 1.4      | 22/07/2026 | Tropeano  | Estrazione PDF AI implementata, BOM Import Service aggiornato con creazione automatica dispositivi e flag CLI, mapping colonne Excel corretto (17 colonne), API token opzionale, relazioni Strapi fixed, tool export aggiunto, 62 test xUnit, bootstrap auto-permissions |
| 1.5      | 29/07/2026 | Tropeano  | Riscrittura da C#/.NET a Python 3.11+. Pipeline BOM: pacchetto ariadne-py con openpyxl (Excel), pdfplumber (PDF), DeepSeek AI, database SQLite locale, upload SFTP. Test suite pytest. Architettura aggiornata ovunque. |
| 1.6      | 12/08/2026 | Tropeano  | Aggiunto parser PDF diretto BOM (regex, senza AI) come percorso primario per PDF testuali. DeepSeek AI declassata a fallback a pagamento, disabilitato di default (DEEPSEEK_ENABLED), max_tokens 2000, log token/costo per chiamata. Rimossi riferimenti Claude/Anthropic. 28 test pytest passanti. |
| 1.7      | 12/08/2026 | Tropeano  | Parser CSV (KiCad/EasyEDA, auto-detect delimitatore), classificazione EEC automatica (16 categorie), controllo duplicati BOM (skip con warning), esportazione DB → Excel. 47 test pytest, 350/350 componenti importati da 5 BOM reali. |
| 1.8      | 12/08/2026 | Tropeano  | Storage dati grezzi MongoDB (bom_files: contenuto + hash sha256 + metadata). Opzionale, graceful degradation offline. 54 test pytest. |
| 1.9      | 12/08/2026 | Tropeano  | Parser OpenDocument (.ods) con schema dinamico. Import BOM reale Devtank HILTOP Motherboard (160/160). 115 test pytest, 93% coverage, 510/510 componenti da 6 BOM reali. |

## Indice

- [Sistema Ariadne di Recupero Materiali Data-Driven](#sistema-ariadne-di-recupero-materiali-data-driven)
  - [Documento di Specifica dei Requisiti di Progetto](#documento-di-specifica-dei-requisiti-di-progetto)
    - [STORIO REVISIONI](#storio-revisioni)
  - [Indice](#indice)
  - [ 1 Introduzione](#-1-introduzione)
    - [ 1.1 Scopo e Campo di Applicazione](#-11-scopo-e-campo-di-applicazione)
    - [ 1.2 Definizioni](#-12-definizioni)
    - [ 1.3 Panoramica del Documento](#-13-panoramica-del-documento)
    - [ 1.4 Bibliografia](#-14-bibliografia)
  - [ 2 Descrizione del Progetto](#-2-descrizione-del-progetto)
    - [ 2.1 Introduzione al Progetto](#-21-introduzione-al-progetto)
    - [ 2.2 Quadro C1-C2-C3](#-22-quadro-c1-c2-c3)
    - [ 2.3 Tecnologie Utilizzate](#-23-tecnologie-utilizzate)
    - [ 2.4 Assunzioni e Vincoli](#-24-assunzioni-e-vincoli)
  - [ 3 Panoramica del Sistema](#-3-panoramica-del-sistema)
    - [ 3.1 Architettura del Sistema](#-31-architettura-del-sistema)
    - [ 3.2 Interfacce del Sistema](#-32-interfacce-del-sistema)
    - [ 3.3 Dati del Sistema](#-33-dati-del-sistema)
      - [ 3.3.1 Input del Sistema](#-331-input-del-sistema)
      - [ 3.3.2 Output del Sistema](#-332-output-del-sistema)
       - [ 3.3.3 Schema del Database (Collection Types Strapi — Fase 1)](#db-schema)
    - [BOM di Riferimento: STEVAL-SPIN3204](#bom-di-riferimento-steval-spin3204)
  - [ 4 Pipeline di Import MDF e Dati](#-4-pipeline-di-import-mdf-e-dati)
    - [ 4.1 Flusso di Import BOM](#-41-flusso-di-import-bom)
    - [ 4.2 Elaborazione e Verifica MDF](#-42-elaborazione-e-verifica-mdf)
    - [ 4.3 Esempi di Query](#-43-esempi-di-query)

## <a id="intro"></a> 1 Introduzione

<details>
    <summary> Il documento di specifica di progetto riflette la progettazione e fornisce indicazioni a realizzatori e sviluppatori del prodotto.</summary>
    Attraverso questo documento, i progettisti comunicano il progetto del prodotto a cui i realizzatori o sviluppatori devono attenersi. La specifica di progetto deve indicare come il progetto soddisfa i requisiti.
</details>

### <a id="purpose"></a> 1.1 Scopo e Campo di Applicazione

<details>
    <summary> Lo scopo di questa sezione è descrivere il fine del documento e il pubblico di riferimento </summary>
    <p>Questo documento definisce le specifiche di progetto per il <b>Sistema Ariadne di Recupero Materiali Data-Driven</b> (Brevetto Italiano n. 102019000014451, Brevetto Europeo n. EP4010822). Traduce i requisiti utente definiti nell'URS in una progettazione tecnica che guida sviluppatori e realizzatori.</p>
    <p><b>Scopo Fase 1:</b> Questa progettazione copre esclusivamente i <b>componenti C1</b> — componenti elettrici/elettronici primari prevalentemente presenti su PCB, ma che in qualche caso si possono ritrovare anche in altre parti di un apparecchio (es. spie acceso/spento, interruttori, potenziometri). In questa fase si farà riferimento solo ai numerosi componenti diversi che si possono trovare sulle PCB, lasciando altri singoli casi a successive integrazioni o revisioni. L'obiettivo è costruire un database SQL strutturato dei materiali presenti in questi componenti, partendo dall'importazione BOM e dall'elaborazione delle Material Declaration Forms (MDF). Funzionalità come riconoscimento OpenCV, parsing AI/LLM, assistenza al disassemblaggio, smistamento materiali e calcolo valori di mercato sono intenzionalmente escluse da questa fase e saranno affrontate in fasi successive della roadmap della piattaforma Ariadne.</p>
    <p><b>Decisione architetturale chiave:</b> Tutti i dati persistenti sono memorizzati in un database gestito tramite **Strapi** (headless CMS, https://strapi.io/). L'accesso ai dati avviene esclusivamente tramite le **API REST** esposte da Strapi. Il database sottostante è PostgreSQL. I file Excel (.xlsx) sono utilizzati esclusivamente come formato di input per importare i dati BOM. La traccia Excel della tesi di Roberto Mantello funge da riferimento logico per la progettazione dello schema, ma il database finale è strutturato in Collection Types Strapi e implementato su PostgreSQL.</p>
</details>

### <a id="def"></a> 1.2 Definizioni

<details>
    <summary> Acronimi e termini chiave usati nel documento </summary>

| Termine | Definizione                                                      |
| ------- | ---------------------------------------------------------------- |
| AEE     | Apparecchiature Elettriche ed Elettroniche                       |
| RAEE    | Rifiuti da AEE (WEEE)                                            |
| BOM     | Bill of Materials / Distinta Base                                |
| MDF     | Materials Declaration Form / Materials Declaration Sheet         |
| DRS     | Design Requirement Specification                                 |
| URS     | User Requirements Specification                                  |
| API     | Application Programming Interface                                |
| REST    | Representational State Transfer                                  |
| openpyxl | Libreria Python per lettura/scrittura file Excel              |
| CRM     | Materie Prime Critiche (Reg. UE 2024/1252)                       |
| EEC     | Electronic Engineering Components (classificazione 16 categorie) |
| CASRN   | Chemical Abstracts Service Registry Number                       |
| LLM     | Large Language Model                                             |
| C1      | Componenti elettrici/elettronici primari                         |
| C2      | Semilavorati / subassemblati                                     |
| C3      | Prodotti finiti pronti per il mercato                            |
| SMD     | Surface Mount Device                                             |
| SMT     | Surface-Mount Technology (tecnologia a montaggio superficiale)   |
| THT     | Through-Hole Technology (componenti con piedini passanti)        |
| RoHS    | Restriction of Hazardous Substances (Dir. 2011/65/EU)            |
| OCR     | Riconoscimento Ottico dei Caratteri                              |

</details>

### <a id="overview"></a> 1.3 Panoramica del Documento

<details>
    <summary> Spiega come è organizzato il documento </summary>
    <p>La Sezione 2 descrive il contesto del progetto, gli obiettivi, le tecnologie e i vincoli, incluso il quadro C1-C2-C3. La Sezione 3 fornisce una panoramica del sistema includendo architettura, interfacce e lo schema del database semplificato per la Fase 1. La Sezione 4 dettaglia la pipeline di import BOM e di elaborazione MDF, incluso il passo opzionale di verifica su Excel intermedio.</p>
</details>

### <a id="biblio"></a> 1.4 Bibliografia

<details>
    <summary> Documenti di riferimento </summary>
    <p>
    • URS – User Requirements Specification (../urs/urs.md)<br>
    • Documento I – Riassunto del Problema e Requisiti Generali (doc1_tropeano.txt)<br>
    • Documento II – Riassunto del Progetto e Requisiti Concordati (doc2.txt)<br>
    • Progetto Ariadne: Requisiti e Specifiche di Sistema (doc5.md)<br>
    • Presentazione Ariadne Digital Path (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)<br>
    • Designators EEC -C1 index -X LUCA 2.xlsx<br>
    • Scheda STM-Steval Spin3204 - BOM di riferimento<br>
    • Email "Materiale visto insieme" (26/06/2026)<br>
    • Email "Aggiornamento file Designators" (26/06/2026)<br>
    • Note di revisione da Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)<br>
    • Regolamento UE Materie Prime Critiche (Regolamento UE 2024/1252)
    </p>
</details>

## <a id="description"></a> 2 Descrizione del Progetto

### <a id="project-intro"></a> 2.1 Introduzione al Progetto

<details>
    <summary> Descrive ad alto livello l'obiettivo del progetto e la soluzione per la Fase 1 </summary>
    <p>Il sistema Ariadne affronta l'inefficienza degli attuali processi di riciclo dei RAEE. La maggior parte degli impianti si basa su triturazione meccanica che permette di recuperare solo 8–10 elementi su 50–60. Il primo passo verso una soluzione — e lo scopo di questa progettazione — è la costruzione di un <b>database SQL strutturato dei materiali presenti nei componenti C1</b>.</p>
    <p><b>Approccio Fase 1:</b></p>
    <p>1. Importare BOM reali di PCB (Excel) per ottenere un elenco di componenti C1<br>
    2. Per ogni componente, recuperare la Material Declaration Form (MDF) dal produttore o distributore<br>
    3. Estrarre i dati dei materiali (nomi in inglese, CASRN, massa mg) dalle MDF<br>
    4. Memorizzare i dati in PostgreSQL tramite Strapi API<br>
    5. Il percorso MDF→DB può includere opzionalmente un passo Excel intermedio per verifica manuale dei dati estratti dall'AI</p>
    <p><b>Decisione architetturale chiave:</b> Il sistema utilizza **Strapi** (headless CMS) con PostgreSQL come database backend. Il template Excel della tesi di Roberto Mantello fornisce una traccia logica per lo schema, ma il database finale è strutturato in Collection Types Strapi e più normalizzato — come da requisito: <i>"Questa è una traccia per l'organizzazione del DB che sarà più strutturato e più capiente."</i> L'accesso ai dati avviene esclusivamente tramite API REST Strapi.</p>
</details>

### <a id="c-framework"></a> 2.2 Quadro C1-C2-C3

<details>
    <summary> Classificazione dei componenti a tre livelli nella piattaforma Ariadne </summary>
    <p>La piattaforma Ariadne classifica i componenti in tre livelli. Questa fase copre solo i C1.</p>

| Livello | Definizione                                                                                                                                           | Esempi                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **C1**  | Componenti elettrici/elettronici primari — forma funzionale minima, non ulteriormente semplificabili/smontabili senza perdere le loro caratteristiche | Resistenze, condensatori, transistor, IC, diodi, connettori, cristalli, LED |
| **C2**  | Semilavorati / subassemblati — unità assemblate che possono essere ulteriormente smontate in componenti C1                                            | Assemblati PCB, moduli alimentazione, assemblaggi display con contenitore   |
| **C3**  | Prodotti finiti pronti per il mercato — dispositivi completi                                                                                          | Cellulari, computer, lavatrici, macchine caffè                              |

<p><b>La Fase 1 copre solo i componenti C1.</b> Le BOM utilizzate sono esclusivamente di PCB, che servono come fonte / elenco di componenti C1 realmente utilizzati nella produzione elettronica. Questo approccio aiuta anche a realizzare un'architettura software già predisposta per dialogare con le altre parti del sistema Ariadne in fasi future.</p>
    <p><b>Nota sul tipo di montaggio:</b> I componenti C1 si distinguono in base alla tecnologia di montaggio sulla PCB. Questa informazione è rilevante per le successive fasi di disassemblaggio e va registrata per ogni componente:</p>
    <p>
    • <b>SMT</b> (Surface-Mount Technology) — componente saldato sulla superficie della scheda. L'acronimo <b>SMD</b> (Surface-Mount Device) si riferisce al componente stesso.<br>
    • <b>THT</b> (Through-Hole Technology) — componente con piedini passanti attraverso fori nella PCB.
    </p>
</details>

### <a id="tech"></a> 2.3 Tecnologie Utilizzate

<details>
    <summary> Descrizione dell'architettura complessiva e dello stack tecnologico per la Fase 1 </summary>
    <p>Il sistema è costruito sul seguente stack tecnologico:</p>

| Layer        | Tecnologia                                                                         |
| ------------ | ---------------------------------------------------------------------------------- |
| Frontend     | React (o altro framework web via Strapi API)                                       |
| Backend API  | **Strapi** (headless CMS, REST/GraphQL API automatiche)                            |
| Database     | SQLite (locale) / PostgreSQL (via Strapi)                                          |
| Import BOM   | **CLI Python (ariadne-py)** — openpyxl (parsing Excel), pdfplumber + pdf_parser (parsing diretto PDF) → SQLite / Strapi API |
| AI/LLM       | **API DeepSeek** — fallback a pagamento per estrazione BOM da PDF, disabilitata di default (DEEPSEEK_ENABLED) |
| Testing      | **pytest** — test che coprono import BOM, estrazione PDF, validazione modelli      |
| Export Tool   | **Ariadne Export** — strumento CLI per esportare database in Excel (openpyxl)      |
| OCR          | Future: riconoscimento documenti per PDF scannerizzati (fase successiva)             |
| Hosting      | Qualsiasi server Python (Linux/Windows) + Strapi server (se utilizzato)            |
   
<p><b>Tecnologie esplicitamente escluse dalla Fase 1:</b> OpenCV (computer vision), OCR per PDF scannerizzati. Saranno introdotte in fasi successive.</p>
</details>

### <a id="constraints"></a> 2.4 Assunzioni e Vincoli

<details>
    <summary> Confini e assunzioni che limitano le scelte progettuali </summary>
    <p>
    • I dati BOM sono forniti dai produttori in formato Excel con colonne: Articolo, Quantità, Reference Designator, Valore Parte, Produttore, Codice Ordinamento Produttore, Fornitore 1/2/3, Codice Ordinamento Fornitore 1/2/3<br>
    • Excel è usato <b>solo come formato di input</b> — tutti i dati sono memorizzati in un database gestito da Strapi (PostgreSQL), accessibile solo tramite API REST<br>
    • Il template Excel della tesi è una <b>traccia logica</b> per la progettazione dello schema; il DB finale è strutturato in Collection Types Strapi e più normalizzato<br>
    • Le Material Declaration Forms (MDF) sono tipicamente in formato PDF e contengono sostanze identificate da CASRN<br>
    • I nomi dei materiali nel DB sono in inglese<br>
    • L'unità di massa standard è il milligrammo (mg)<br>
    • Il sistema opera su soli componenti C1 (componenti a livello PCB) in Fase 1<br>
    • Lo sviluppo è in Python 3.11+<br>
    • I reference designator seguono lo standard IEEE/ANSI ma devono gestire varianti specifiche dei CAD<br>
    • La categoria EEC è distinta dal reference designator: un reference designator (es. "R") identifica il tipo di componente (resistore), mentre la categoria EEC (es. 12 "Resistors") ne definisce la classificazione merceologica. Più designator possono appartenere alla stessa categoria EEC. Questa distinzione è necessaria perché la BOM fornisce il designator, ma il sistema deve poter classificare e raggruppare i componenti per categoria EEC a fini di analisi dei materiali.<br>
    • Per ogni componente deve essere registrato il tipo di montaggio: SMT (Surface-Mount Technology, componente saldato sulla superficie della PCB) o THT (Through-Hole Technology, componente con piedini passanti attraverso fori nella PCB). Questa informazione è rilevante per le successive fasi di disassemblaggio e trattamento.
    </p>
</details>

## <a id="system-overview"></a> 3 Panoramica del Sistema

<details>
    <summary> Descrizione ad alto livello della struttura e del comportamento del sistema </summary>
    <p>Il sistema Ariadne (Fase 1) è una piattaforma web di gestione dati focalizzata sull'importazione di BOM, l'elaborazione di Material Declaration Forms e la memorizzazione dei dati di composizione materiale in un database SQL strutturato. Il sistema risponde a <b>quali, quanti e dove</b> si trovano i materiali nei componenti C1 di un dispositivo.</p>
    <p><b>Nota sul "dove":</b> A livello di componente C1, il "dove" indica <b>in quale componente</b> (quale riga di BOM, identificata dal reference designator) si trova un determinato materiale, non la posizione interna al componente stesso. Per quanto alcune MDF riportino la distribuzione interna dei materiali all'interno di un singolo componente (es. incapsulamento, terminali, die), questa distinzione non è tecnicamente rilevante ai fini del recupero — non è possibile separare elementi così intimamente connessi dentro un singolo componente (es. resistore, microprocessore). Per ciascun elemento/materiale si riporterà quindi il suo totale presente in ogni singolo componente.</p>
</details>

### <a id="architecture"></a> 3.1 Architettura del Sistema

<details>
    <summary> Descrizione e diagramma dell'architettura di sistema </summary>
    <p>Il sistema segue un'architettura a tre livelli:</p>
    <pre>
[Client Web] ↔ [API Gateway] ↔ [Servizio BOM/MDF]
                                 ├── [Database SQL]
                                 └── [Logger di Audit (base)]

Pipeline Dati:
  BOM Excel → [Parser openpyxl] → SQLite / Strapi API → PostgreSQL (elenco componenti)
  BOM PDF → [Estrazione Testo pdfplumber] → [Parser Diretto pdf_parser] → SQLite / Strapi API (componenti)
  BOM PDF → [pdfplumber] → [API DeepSeek AI — fallback a pagamento, disabilitata di default] → JSON → SQLite / Strapi API
  MDF PDF → [Inserimento Manuale via UI] → Strapi API POST → PostgreSQL (materiali)
    </pre>
    <p>Il sistema utilizza una pipeline CLI Python (ariadne-py) per l'import BOM. I dati sono memorizzati localmente in SQLite e opzionalmente sincronizzati su Strapi API + PostgreSQL quando configurato. La pipeline MDF supporta sia l'inserimento manuale che l'estrazione assistita da AI con un passo Excel intermedio opzionale per la verifica dei dati.</p>

</details>

### <a id="interfaces"></a> 3.2 Interfacce del Sistema

<details>
    <summary> Interfacce esterne e punti di interazione </summary>
    <p>
    • <b>Interfaccia Utente:</b> UI web accessibile via browser per inserimento dati, importazione e interrogazioni<br>
    • <b>Import File:</b> Caricamento BOM Excel tramite openpyxl; caricamento BOM PDF (parser diretto via pdfplumber, DeepSeek AI come fallback a pagamento se abilitata)<br>
    • <b>Interfaccia API:</b> Endpoint REST per gestione dispositivi, import BOM, inserimento dati materiali, interrogazioni<br>
    • <b>Interfaccia Database:</b> API REST Strapi (CRUD automatiche) per storage persistente su PostgreSQL<br>
    • <b>Export Excel (opzionale):</b> Export intermedio per verifica manuale dati MDF prima del commit nel DB<br>
    • <b>Export Database (CLI):</b> StrapiExport genera Excel a 6 fogli dall'API Strapi (Summary, EEC Categories, Reference Designators, BOM Entries, Devices, Audit Logs)
    </p>
</details>

### <a id="data"></a> 3.3 Dati del Sistema

<details>
    <summary> Panoramica del modello dati e flusso dei dati </summary>
    <p>Il sistema gestisce: catalogo dispositivi/PCB, dati BOM per componenti C1, dichiarazioni materiali con sostanze identificate da CASRN, categorie EEC e reference designator — tutto memorizzato in Collection Types Strapi su PostgreSQL, accessibili via API REST. Il flusso dati va dall'import BOM attraverso l'identificazione dei componenti fino al recupero MDF e alla memorizzazione dei dati materiali.</p>
</details>

#### <a id="inputs"></a> 3.3.1 Input del Sistema

<details>
    <summary> Tipi di dati che il sistema riceve </summary>
    <p>
    • File BOM Excel (colonne: Articolo, Quantità, Reference Designator, Valore Parte, Produttore, Codice Ordinamento Produttore, Fornitore 1, Codice Ordinamento Fornitore 1, Fornitore 2, Codice Ordinamento Fornitore 2, Fornitore 3, Codice Ordinamento Fornitore 3) — parsato tramite EPPlus, memorizzato in SQL DB; Excel non è mai usato come storage persistente<br>
    • Metadati dispositivo: marca, nome modello, produttore, anno di produzione<br>
    • Dati delle Material Declaration Forms (MDF): nome materiale (inglese), CASRN, massa (mg), classificazione elemento/composto<br>
    • I dati MDF possono essere inseriti: (a) manualmente tramite UI, (b) tramite estrazione AI con verifica Excel intermedia opzionale<br>
    • Numeri di catalogo dei distributori (Fornitore 1/2/3) per tracciamento percorso sourcing MDF
    </p>
</details>

#### <a id="outputs"></a> 3.3.2 Output del Sistema

<details>
    <summary> Tipi di dati che il sistema produce </summary>
    <p>
    • Risultati interrogazioni: quali materiali, quanti (massa totale e per componente), dove (quale componente/designator) in un dispositivo<br>
    • Report composizione materiali per dispositivo/PCB<br>
    • Opzionale: export Excel intermedio per verifica dati MDF prima del commit nel DB<br>
    • Log di audit base per operazioni di inserimento dati
    </p>
</details>

#### <a id="db-schema"></a> 3.3.3 Schema del Database (Collection Types Strapi — Fase 1)

Lo schema seguente definisce i Collection Types Strapi per la Fase 1: memorizzazione dati componenti C1. I Collection Type per disassemblaggio, smistamento, valori di mercato e gestione distributori sono esclusi da questa fase. L'accesso ai dati avviene tramite API REST Strapi.

**PCB / Device**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| DeviceId | int (PK, IDENTITY) | Chiave primaria | 1 |
| Brand | nvarchar(100) | Marca dispositivo | STMicroelectronics |
| ModelName | nvarchar(200) | Nome modello | STEVAL-SPIN3204 |
| Manufacturer | nvarchar(200) | Nome produttore | STMICROELECTRONICS |
| YearOfProduction | int | Anno di produzione | 2021 |
| Notes | nvarchar(500) | Note aggiuntive | Rev 211 |

**BOMEntry**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| BOMEntryId | int (PK, IDENTITY) | Chiave primaria | 1 |
| DeviceId | int (FK) | Riferimento a PCB/Device | 1 |
| ItemNumber | int | Numero riga nella BOM | 1 |
| Quantity | int | Quantità componente | 14 |
| ReferenceDesignator | nvarchar(500) | Designator | C1,C5,C7,C8,C9,C11 |
| MountingType | nvarchar(10) | Tipo montaggio: SMT, THT | SMT |
| PartValue | nvarchar(100) | Valore del componente | 100 nF |
| Manufacturer | nvarchar(200) | Produttore del componente | KEMET |
| ManufacturerOrderCode | nvarchar(200) | Codice ordinamento produttore | C0603C104K5RACTU |
| Supplier1 | nvarchar(100) | Primo fornitore | DIGIKEY |
| Supplier1OrderCode | nvarchar(200) | Catalogo fornitore 1 | PCE3820CT-ND |
| Supplier2 | nvarchar(100) | Secondo fornitore | MOUSER |
| Supplier2OrderCode | nvarchar(200) | Catalogo fornitore 2 | 12345 |
| Supplier3 | nvarchar(100) | Terzo fornitore | FARNELL |
| Supplier3OrderCode | nvarchar(200) | Catalogo fornitore 3 | 67890 |
| DesignatorCode | nvarchar(10) | Codice designator (R, C, U, Q, D...) | C |
| EEC_CategoryId | int (FK) | Categoria EEC (1-16) | 2 |
| Notes | nvarchar(500) | Note aggiuntive | Appro ADEX |

**ComponentMaterial**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| ComponentMaterialId | int (PK, IDENTITY) | Chiave primaria | 1 |
| BOMEntryId | int (FK) | Riferimento a BOMEntry | 1 |
| MaterialId | int (FK) | Riferimento a Material | 5 |
| Mass_mg | decimal(12,4) | Massa in mg | 12.5000 |
| Note | nvarchar(500) | Nota (lega, CASRN alternativo) | Wire termination |
| SourceMDF | nvarchar(500) | Nome file MDF di origine | MDF_KEMET_C0603.pdf |

**Material**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| MaterialId | int (PK, IDENTITY) | Chiave primaria | 1 |
| MaterialName | nvarchar(200) | Nome materiale (inglese) | Copper |
| CASRN | nvarchar(20) | CAS Registry Number | 7440-50-8 |
| Category | nvarchar(20) | 'element' o 'compound' | element |

**ReferenceDesignator**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| DesignatorCode | nvarchar(10) (PK) | Codice designator | R |
| Name | nvarchar(100) | Nome tipo componente | Resistor |
| Description | nvarchar(500) | Descrizione completa | Resistenza |
| EEC_CategoryId | int (FK) | Categoria EEC corrispondente | 12 |

**EEC_Category**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| CategoryId | int (PK) | Numero categoria (1-16) | 12 |
| Name | nvarchar(100) | Nome categoria | Resistors |
| Subcategories | nvarchar(max) | Lista JSON sottocategorie | ["Film","Metal Foil","Network Arrays","Jumper","Wire Wound"] |

**AuditLog**
| Colonna | Tipo | Descrizione | Esempio |
|---------|------|-------------|---------|
| LogId | int (PK, IDENTITY) | Chiave primaria | 1 |
| Timestamp | datetime | Timestamp evento | 2026-06-28 10:30:00 |
| UserId | nvarchar(100) | Identificativo utente | luca.tropeano |
| DeviceId | int (FK) | Riferimento a Device | 1 |
| Action | nvarchar(200) | Azione eseguita | BOM_IMPORT |
| Details | nvarchar(max) | Dettagli aggiuntivi | 74 componenti importati |

### BOM di Riferimento: STEVAL-SPIN3204

| Articolo | Q.tà | Riferimento                                        | Valore Parte     | Package        | Produttore         | Montaggio |
| -------- | ---- | -------------------------------------------------- | ---------------- | -------------- | ------------------ | --------- |
| 1        | 14   | C1,C5,C7,C8,C9,C11,C20,C26,C27,C28,C29,C33,C34,C37 | 100 nF           | 0603           | KEMET              | SMT       |
| 2        | 1    | C2                                                 | 22 uF            | L8.3_W8.3_H9.5 | PANASONIC          | SMT       |
| 21       | 1    | D1                                                 | STPS0560Z        | SOD123         | STMICROELECTRONICS | SMT       |
| 22       | 7    | D2,D9,D10,D11,D12,D13,D14                          | BAT30KFILM       | SOD523         | STMICROELECTRONICS | SMT       |
| 36       | 1    | LD1                                                | RED-GREEN        | PLCC4          | AVAGO              | SMT       |
| 37       | 1    | L1                                                 | 22uH             | L3_W3_H1.5     | BOURNS             | SMT       |
| 40       | 6    | Q1-Q6                                              | N-MOS STD140N6F7 | DPAK           | STMICROELECTRONICS | SMT       |
| 41       | 1    | Q7                                                 | NPN BC847BLT1G   | SOT23          | ON SEMICONDUCTOR   | SMT       |
| 66       | 3    | SW1,SW2,SW3                                        | 430483025816     | L6.2_W6.2_H2.5 | WURTH ELEKTRONIK   | SMT       |
| 70       | 1    | U1                                                 | STSPIN32F0B      | VFQFPN48       | STMICROELECTRONICS | SMT       |
| 73       | 1    | U4                                                 | STM32F103CBT6    | LQFP48         | STMICROELECTRONICS | SMT       |
| 74       | 1    | X1                                                 | 8MHz             | L3.2_W2.5      | NDK                | SMT       |

**Totali:** 199 componenti, 74 tipi unici (soli componenti C1) — tutti a montaggio superficiale (SMT) in questa BOM

## <a id="mdf-pipeline"></a> 4 Pipeline di Import MDF e Dati

### <a id="bom-import"></a> 4.1 Flusso di Import BOM

<details>
    <summary> Flusso di lavoro per importare dati BOM da file (inizialmente Excel per la fase di prova) </summary>
    <p><b>Passo 1:</b> L'utente carica il file BOM (inizialmente in formato Excel per la fase di prova, tramite l'interfaccia web)<br>
    <b>Passo 2:</b> BOMService parsa il file tramite EPPlus, valida la struttura delle colonne<br>
    <b>Passo 3:</b> Ogni componente viene classificato:<br>
     - DesignatorValidator controlla il reference designator (R, C, U, Q, D, ecc.)<br>
     - EECClassifier mappa il designator alla corrispondente categoria EEC (1-16)<br>
    <b>Passo 4:</b> Le entità Device e BOMEntry vengono create/aggiornate in Strapi tramite API REST<br>
    <b>Passo 5:</b> Report di validazione restituito all'utente (conteggio successi, avvisi, designator sconosciuti)</p>
</details>

### <a id="mdf-processing"></a> 4.2 Elaborazione e Verifica MDF

<details>
    <summary> Il percorso critico: dalla Material Declaration Form al PostgreSQL (via Strapi) </summary>
    <p>Questo è il percorso critico del sistema. Due approcci sono supportati:</p>

    <p><b>Approccio A — Inserimento Manuale:</b><br>
    (1) L'operatore recupera la MDF PDF dal sito del produttore o distributore<br>
    (2) Legge i dati dei materiali dal PDF manualmente<br>
    (3) Inserisce nome materiale (inglese), CASRN, massa (mg) tramite UI web<br>
    (4) Il sistema valida il formato CASRN e memorizza i dati in PostgreSQL (via Strapi)</p>
    
    <p><b>Approccio B — Estrazione Assistita da AI (futuro):</b><br>
    (1) L'AI estrae il testo dalla MDF PDF tramite API LLM<br>
    (2) Restituisce JSON strutturato con i dati dei materiali<br>
    (3) Il JSON viene parsato e validato<br>
    (4) I dati vengono scritti in PostgreSQL tramite Strapi API</p>
    
    <p><b>Approccio C — AI Diretto a PostgreSQL (via Strapi) (futuro):</b><br>
    (1) L'AI estrae e valida i dati automaticamente con modelli a maggiore accuratezza<br>
    (2) I dati vengono scritti direttamente in PostgreSQL (via Strapi)<br>
    (3) Richiede un modello AI maturo con alta accuratezza — pianificato per fasi successive</p>

</details>

### <a id="queries"></a> 4.3 Esempi di Query

<details>
    <summary> Query SQL chiave per il requisito "quali, quanti, dove" </summary>

    <p><b>Quali materiali sono in un dispositivo?</b></p>
    <pre>SELECT DISTINCT m.MaterialName, m.CASRN, m.Category

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'</pre>

    <p><b>Quanto (massa) di ogni materiale?</b></p>
    <pre>SELECT m.MaterialName, SUM(cm.Mass_mg) AS TotalMass_mg

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'
GROUP BY m.MaterialName
ORDER BY TotalMass_mg DESC</pre>

    <p><b>Dove (quale componente) si trova un materiale specifico?</b></p>
    <pre>SELECT b.ReferenceDesignator, b.PartValue, b.Manufacturer, cm.Mass_mg

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
    WHERE d.ModelName = 'STEVAL-SPIN3204' AND m.CASRN = '7440-50-8'</pre>

</details>

## <a name="strapi-design"></a> 5 Progettazione Collection Types Strapi

<details>
    <summary> Specifica dettagliata dei Collection Types per l'implementazione su Strapi </summary>

### 5.1 Device

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| brand | Text | required, minLength(1) | Marca del dispositivo |
| modelName | Text | required, unique | Nome modello (univoco per identificare il dispositivo) |
| manufacturer | Text | required | Nome del produttore |
| yearOfProduction | Integer | required, min(1900), max(2030) | Anno di produzione |
| notes | RichText | optional | Note libere |

**Permessi:** full CRUD per Admin e API Key; lettura per Public (se necessario).

### 5.2 BOMEntry

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| itemNumber | Integer | required | Numero riga dalla BOM |
| quantity | Integer | required, min(1) | Quantità di quel componente |
| referenceDesignator | Text | required | Designator separati da virgola |
| mountingType | Enumeration | required, enum: SMT, THT | Tipo montaggio |
| partValue | Text | optional | Valore del componente (es. 100 nF) |
| manufacturer | Text | optional | Produttore del componente |
| manufacturerOrderCode | Text | optional | Codice ordinamento produttore |
| supplier1 | Text | optional | Primo fornitore |
| supplier1OrderCode | Text | optional | Catalogo fornitore 1 |
| supplier2 | Text | optional | Secondo fornitore |
| supplier2OrderCode | Text | optional | Catalogo fornitore 2 |
| supplier3 | Text | optional | Terzo fornitore |
| supplier3OrderCode | Text | optional | Catalogo fornitore 3 |
| designatorCode | Text | optional | Codice designator (R, C, U...) |
| notes | RichText | optional | Note aggiuntive |

**Relazioni:**
- device (manyToOne → Device) — required
- eecCategory (manyToOne → EEC_Category) — required
- componentMaterials (oneToMany → ComponentMaterial)

**Permessi:** create/update tramite API Key (import BOM), lettura tramite Public API (query).

### 5.3 ComponentMaterial

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| massMg | Decimal | required, min(0) | Massa in mg |
| note | Text | optional | Lega, CASRN alternativo |
| sourceMdf | Text | optional | Nome file MDF di origine |

**Relazioni:**
- bomEntry (manyToOne → BOMEntry) — required
- material (manyToOne → Material) — required

**Permessi:** create/update tramite API Key (inserimento MDF), lettura Public.

### 5.4 Material

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| materialName | Text | required, unique | Nome materiale (sempre in inglese) |
| casrn | Text | optional, unique | CAS Registry Number (formato: xxx-yy-z) |
| category | Enumeration | required, enum: element, compound | Classificazione |

**Validazione CASRN:** Formato `xxx-yy-z` dove x=2-7 cifre, y=2 cifre, z=1 cifra di controllo.

**Permessi:** create/update tramite API Key, lettura Public.

### 5.5 ReferenceDesignator

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| designatorCode | UID | required, unique | Codice designator (R, C, U...) |
| name | Text | required | Nome (Resistor, Capacitor...) |
| description | Text | optional | Descrizione completa |

**Relazioni:**
- eecCategory (manyToOne → EEC_Category) — required

### 5.6 EEC_Category

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| categoryId | Integer | required, unique, min(1), max(16) | Numero categoria 1-16 |
| name | Text | required | Nome categoria |
| subcategories | JSON | optional | Lista di sottocategorie |

**Relazioni:**
- referenceDesignators (oneToMany → ReferenceDesignator)
- bomEntries (oneToMany → BOMEntry)

### 5.7 AuditLog

| Campo | Tipo Strapi | Vincoli | Note |
|-------|------------|---------|------|
| timestamp | DateTime | required | Data/ora evento |
| userId | Text | required | Identificativo utente |
| action | Text | required | Azione (es. BOM_IMPORT, MDF_INSERT) |
| details | RichText | optional | Dettagli aggiuntivi |

**Relazioni:**
- device (manyToOne → Device) — required

**Permessi:** solo scrittura tramite backend, lettura Admin.

### 5.8 Riepilogo Permessi

| Ruolo | Collection Types accessibili | Operazioni |
|-------|---------------------------|------------|
| Public API (anonimo) | Device, BOMEntry, ComponentMaterial, Material, ReferenceDesignator, EEC_Category, AuditLog | CRUD completo (tutte le operazioni) |
| API Key (import BOM) | Device, BOMEntry, ComponentMaterial, Material, EEC_Category | POST, PUT (import dati) |
| Admin (Strapi admin UI) | Tutti | CRUD completo, gestione permessi |

**Nota:** L'API token è opzionale — il ruolo Public ha permessi CRUD completi configurati automaticamente dal bootstrap script (`src/index.ts`). Quando l'API token è vuoto o inizia con `<`, lo `StrapiClient` salta l'header `Authorization` e si affida ai permessi CRUD del ruolo Public.

</details>

## <a name="bom-import-design"></a> 6 Progettazione Pipeline BOM (Python)

<details>
    <summary> Specifica della pipeline BOM Python (Excel via openpyxl + PDF via parser diretto / fallback DeepSeek AI) → SQLite / Strapi API </summary>

### 6.1 Architettura della Pipeline

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────┐
│ BOM Excel   │────▶│ Orchestrator     │────▶│ Database    │────▶│ SQLite /     │
│ (.xlsx)     │     │ (Python)         │     │ (SQLite)    │     │ Strapi API   │
└─────────────┘     └──────────────────┘     └─────────────┘     └──────┬───────┘
                           │                                            │
┌─────────────┐            │                                            ▼
│ MDF PDF     │──▶ pdfplumber ──▶ pdf_parser (regex) ──▶ BOMEntry  │
│ (.pdf)      │   Extract     │  (primario, senza AI)  (Pydantic)    │
└─────────────┘            │                                            │
                           │  └─ se 0 entries e DEEPSEEK_ENABLED=true  ▼
                           │        └─▶ DeepSeek API ──▶ JSON parse │
                           │                    BOMEntry + usage/costo  │
                     ┌──────────────┐                           ┌──────────────┐
                     │ Validazione   │                           │ SQLite DB    │
                     │ Designator    │                           │ (locale) /   │
                     │ Categoria EEC │                           │ PostgreSQL   │
                     └──────────────┘                           └──────────────┘
```

### 6.2 Moduli Principali

**main.py** — punto di ingresso CLI (click):
- `ariadne process <file> [--brand] [--model] [--manufacturer] [--year]` — elabora file BOM
- `ariadne stats` — mostra statistiche database
- Rileva automaticamente il formato file (.xlsx / .pdf) dall'estensione
- Crea un modello `Device` Pydantic dai flag CLI e invia a `Orchestrator`

**Orchestrator** — coordinatore del processo (ariadne/orchestrator.py):
- `process_file(file_path, device)` → `ImportResult` — smista a flusso Excel o PDF
- `_process_excel(file_path, device)` — chiama `parse_excel_bom()` (openpyxl), poi `_import_entries()`
- `_process_pdf(file_path, device)` — chiama `extract_text_from_pdf()` (pdfplumber), poi prova `parse_pdf_bom_text()` (parser diretto); se 0 entries e `deepseek.enabled` fa fallback a `DeepSeekClient.extract_bom()`; poi `_import_entries()`
- `_import_entries(entries, device, result=None)` — logica condivisa: crea/recupera dispositivo in SQLite, inserisce BOM entries; mantiene il risultato di base così i warning PDF (costo AI) non vengono persi

**excel_parser.py** — parsing Excel BOM:
- `parse_excel_bom(file_path)` → `list[BOMEntry]`
- Usa openpyxl per leggere file `.xlsx`
- Intestazioni riga 6, mapping 17 colonne, rilevamento automatico SMT/THT dalla colonna Package

**pdf_extractor.py** — estrazione testo da PDF:
- `extract_text_from_pdf(pdf_path)` → `str`
- `extract_text_from_pdf_stream(stream)` → `str`
- Usa pdfplumber per estrazione testo nativa da PDF
- Restituisce testo separato per pagina (non gestisce PDF scannerizzati/immagini)

**pdf_parser.py** — parser diretto BOM (senza AI, percorso primario):
- `parse_pdf_bom_text(text)` → `list[BOMEntry]`
- Basato su regex: riconosce designator standard (R, C, L, D, U, J, X, Q, SW, LED...), più designator per riga (`C1,C5,C7`), quantità `2x`, valori con unità (`100nF`, `4.7k`, `2u2`)
- Rileva package da ~100+ formati noti (0603, SOT-23, LQFP, QFN, SOIC; THT: DIP/SIP/TO-)
- Riconoscimento manufacturer, deduzione SMT/THT dal package, gestione separatori di pagina

**ai_client.py (DeepSeekClient)** — integrazione API DeepSeek (fallback a pagamento, disabilitata di default):
- `extract_bom(text, system_prompt)` → `AIExtractionResult(entries, usage)`
- Comunica con l'API DeepSeek (`/v1/chat/completions`, compatibile OpenAI)
- `AIUsage` riporta token prompt/completion/total + **costo stimato USD per chiamata** (loggato)
- Usata solo se `DEEPSEEK_ENABLED=true` e il parser diretto non ha trovato nulla

**database.py** — wrapper database SQLite:
- `find_or_create_device(device)` → `int` (device_id)
- `insert_bom_entry(device_id, entry)` → `int` (entry_id)
- `get_stats()` → `dict` con conteggi device/BOM/materiali
- Usa SQLite tramite `sqlite3` (libreria standard)

**models.py** — modelli dati Pydantic:
- `BOMEntry` — Item, Quantity, ReferenceDesignator, PartValue, Package, Manufacturer, ecc.
- `Device` — Brand, ModelName, Manufacturer, YearOfProduction
- `ImportResult` — TotalRows, ImportedRows, FailedRows, Success (calcolato)

**sftp_client.py** — upload SFTP (paramiko):
- `upload_file(local_path, remote_name)` → `str` (percorso remoto)
- Supporto context manager

**config.py** — configurazione da ambiente:
- `AppConfig` → `DeepSeekConfig`, `StrapiConfig`, `SFTPConfig`, `DatabaseConfig`
- Carica automaticamente file `.env` tramite python-dotenv

### 6.3 Flusso di Esecuzione — Excel

```
1. Carica file BOM (.xlsx) via openpyxl
2. Parsa intestazioni riga 6, itera righe dati (min_row=7)
3. Per ogni riga con Item valido:
   a. Leggi valori celle per indice colonna:
      - Col 1: Item (int)
      - Col 2: Qty (int)
      - Col 3: Reference (stringa)
      - Col 5: Part/Value (opzionale)
      - Col 9: Package → rileva SMT/THT (DIP/SIP/TO- → THT, altrimenti SMT)
      - Col 10: Manufacturer (opzionale)
      - Col 11: Mfr Order Code (opzionale, convertito in stringa)
      - Col 12: Notes (opzionale)
      - Col 13: Supplier 1 (opzionale)
      - Col 14: Supplier 1 Order Code (opzionale)
   b. Costruisci modello BOMEntry Pydantic
4. Orchestrator._import_entries():
   a. Database.find_or_create_device() → device_id
   b. Per ogni entry: Database.insert_bom_entry(device_id, entry)
5. Restituisci ImportResult
```

### 6.4 Flusso di Esecuzione — PDF → Parser Diretto / Fallback DeepSeek AI

```
1. pdf_extractor.extract_text_from_pdf(percorso_pdf) → testo grezzo separato per pagina
   Se nessun testo estratto → PDF scannerizzato/immagine, non ancora supportato (OCR/AI pianificato)
2. pdf_parser.parse_pdf_bom_text(testo) → list[BOMEntry]   (primario, gratis)
   a. Se trovate entries → vai al passo 5 (la AI NON viene chiamata)
3. Se parse_pdf_bom_text ha restituito 0 entries:
   a. Se DEEPSEEK_ENABLED=false → errore con warning, nessuna chiamata API
   b. Se DEEPSEEK_ENABLED=true → DeepSeekClient.extract_bom(testo, system_prompt)
      → AIExtractionResult(entries, usage); costo/token loggati nei warning
4. Parsa risposta JSON DeepSeek → oggetti BOMEntry validati
5. Orchestrator._import_entries():
   a. Database.find_or_create_device() → device_id
   b. Per ogni entry: Database.insert_bom_entry(device_id, entry)
6. Restituisci ImportResult (warning preservati)
```

### 6.5 Mapping Colonne Excel → BOMEntry

La BOM Excel reale (`Scheda STM-Steval Spin3204 - Copia x Luca.xlsx`) ha **17 colonne** con intestazioni alla riga 6. Mapping:

| Colonna Excel | Intestazione | Campo BOMEntry | Note |
|---------------|-------------|----------------|------|
| 1 | Item | item_number | int parse — salta righe non numeriche |
| 2 | Qty | quantity | int parse |
| 3 | Reference | reference_designator | Designator separati da virgola |
| 5 | Part/Value | part_value | Valore del componente (es. 100 nF) |
| 9 | Package | mounting_type | DIP/SIP/TO- → THT, altrimenti SMT |
| 10 | Manufacturer | manufacturer | Produttore del componente |
| 11 | Mfr Order Code | manufacturer_order_code | Stringa (celle int convertite automaticamente) |
| 12 | Notes | notes | Note a testo libero |
| 13 | Supplier | supplier | Primo fornitore |
| 14 | Supplier Code | supplier_order_code | Catalogo fornitore |

Le colonne 4 (Description), 6 (Footprint), 7 (Quantità in stock), 8 (Prezzo unitario), 15-17 (dati fornitore aggiuntivi) sono presenti nel file ma non mappate.

### 6.6 Schema Database (SQLite)

```sql
CREATE TABLE device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL DEFAULT '',
    model_name TEXT NOT NULL DEFAULT '',
    manufacturer TEXT NOT NULL DEFAULT '',
    year_of_production INTEGER,
    notes TEXT
);

CREATE TABLE bom_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    item_number INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    reference_designator TEXT NOT NULL,
    part_value TEXT,
    package TEXT,
    manufacturer TEXT,
    manufacturer_order_code TEXT,
    supplier TEXT,
    supplier_order_code TEXT,
    notes TEXT,
    mounting_type TEXT NOT NULL DEFAULT 'SMT',
    designator_code TEXT,
    eec_category_id INTEGER,
    FOREIGN KEY (device_id) REFERENCES device(id)
);
```

### 6.7 Test Unitari (pytest)

Test suite in `ariadne-py/tests/` usando **pytest**:

| File Test | # Test | Cosa verifica |
|-----------|--------|---------------|
| test_models.py | 6 | Default BOMEntry, modello completo, default Device, ImportResult success/failure |
| test_excel_parser.py | 3 | Rilevamento mounting type (SMT, THT, sconosciuto) |
| test_pdf_parser.py | 10 | Parsing BOM PDF diretto (designator, quantità, package, rilevamento THT, manufacturer, campione reale) |
| test_ai_client.py | 6 | Parsing risposta DeepSeek (JSON, markdown-fenced, campi null) + tracking usage/costo |
| test_orchestrator.py | 5 | Flussi Excel/PDF, AI disabilitata di default, fallback AI se abilitata |

### 6.8 Modelli Pydantic

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

### 6.9 Uso CLI

```
ariadne process <file> [--brand X] [--model X] [--manufacturer X] [--year N]

  .xlsx  — import diretto da Excel
  .pdf   — parser diretto (regex); fallback DeepSeek AI solo se DEEPSEEK_ENABLED=true

Options:
  --brand         Marca del dispositivo (es. STM)
  --model         Modello del dispositivo (es. STEVAL-SPIN3204)
  --manufacturer  Produttore del dispositivo
  --year          Anno di produzione
```

```
ariadne stats  — Mostra statistiche database (conteggi device/BOM/materiali)
```

</details>

## <a name="export-tool"></a> 7 Strumento Export Database

<details>
    <summary> Strumento CLI per esportare il database in Excel (importato da versione C#, da riscrivere in Python) </summary>

### 7.1 Panoramica

L'attuale tool di export (`src/main/Tools/`, C# con EPPlus) esporta i dati Strapi in un workbook Excel formattato con 6 fogli. Un equivalente Python tramite openpyxl è pianificato.

### 7.2 Fogli Generati

| Foglio | Contenuto |
|--------|-----------|
| Summary | Data export, conteggio record per tabella, ripartizione BOM per designator |
| EEC Categories | Tutte le 16 categorie EEC con sottocategorie |
| Reference Designators | Tutti i 19 designator con mapping categoria EEC |
| BOM Entries | BOM completa con tutti i campi, auto-filter attivato |
| Devices | Tutti i dispositivi/PCB |
| Audit Logs | Storico operazioni di import |

### 7.3 Architettura (versione C# corrente)

- Usa `HttpClient` per recuperare tutti i dati dall'API REST Strapi con paginazione
- Usa EPPlus per generare Excel con intestazioni formattate (sfondo blu, testo bianco)
- Output in `exports/StrapiExport_YYYYMMDD_HHmmss.xlsx`
- Apre automaticamente il file generato al termine

</details>
