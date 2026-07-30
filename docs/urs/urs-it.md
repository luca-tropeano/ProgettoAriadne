### Documento di Specifica dei Requisiti Utente

##### DIBRIS – Università di Genova. Scuola Politecnica, Corso di Ingegneria del Software 80154

**VERSIONE : 1.4**

**Autori**
Tropeano Luca

**STORIO REVISIONI**

| Versione | Data       | Autori   | Note                                                                      |
| -------- | ---------- | -------- | ------------------------------------------------------------------------- |
| 1.0      | 27/06/2026 | Tropeano | Prima bozza completa basata sui file di progetto                          |
| 1.1      | 28/06/2026 | Tropeano | Revisione dopo feedback Rosario — scope focalizzato su soli componenti C1 |
| 1.2      | 02/07/2026 | Tropeano | Revisione feedback Rosario v2: C1 definito, SMT/THT, RoHS, algoritmi predittivi, allineamento URS/DRS |
| 1.3      | 02/07/2026 | Tropeano | Integrazione Strapi: passaggio da SQL Server diretto a Strapi headless CMS + PostgreSQL, accesso DB tramite API REST |
| 1.4      | 22/07/2026 | Tropeano | Estrazione PDF AI implementata (FR10, NFR6 aggiornati), collegamento/creazione automatica dispositivi (FR8), mapping colonne Excel corretto, API token opzionale, tool export aggiunto, flag CLI --brand/--model/--manufacturer/--year |

# Indice

- [Indice](#indice)
  - [1. Introduzione](#1-introduzione)
    - [1.1 Scopo del Documento](#11-scopo-del-documento)
    - [1.2 Definizioni e Acronimi](#12-definizioni-e-acronimi)
    - [1.3 Riferimenti](#13-riferimenti)
  - [2. Descrizione del Sistema](#2-descrizione-del-sistema)
    - [2.1 Contesto e Motivazioni](#21-contesto-e-motivazioni)
    - [2.2 Scopo e Obiettivi di Progetto](#22-scopo-e-obiettivi-di-progetto)
    - [2.3 Quadro C1-C2-C3](#23-quadro-c1-c2-c3)
    - [2.4 Classificazione Componenti EEC](#24-classificazione-componenti-eec)
    - [2.5 Standard Designators](#25-standard-designators)
  - [3. Requisiti](#3-requisiti)
    - [3.1 Stakeholder](#31-stakeholder)
    - [3.2 Requisiti Funzionali](#32-requisiti-funzionali)
    - [3.3 Requisiti Non Funzionali](#33-requisiti-non-funzionali)
    - [3.4 Requisiti dei Dati](#34-requisiti-dei-dati)

<a id="p1"></a>

## 1. Introduzione

<a id="sp1.1"></a>

### 1.1 Scopo del Documento

Questo documento definisce i requisiti utente per il **Sistema Ariadne di Recupero Materiali Data-Driven** (Brevetto Italiano n. 102019000014451, Brevetto Europeo n. EP4010822).

L'obiettivo principale, definito al **Punto C1** dello schema del flusso dati Ariadne, è la creazione di un **database SQL strutturato** contenente l'elenco dettagliato dei materiali presenti nei **componenti C1** — componenti elettrici ed elettronici nella loro forma funzionale minima, non ulteriormente semplificabili/smontabili senza perdere le loro caratteristiche (es. resistenze, condensatori, transistor, IC, diodi, connettori, cristalli). Il DB sarà collegato alla piattaforma Ariadne per determinare **quali, quanti e dove** si trovano i materiali recuperabili all'interno di ogni apparecchio.

**Nota sul "dove":** A livello di componente C1, "dove" indica **in quale componente** (quale riga di BOM, identificata dal reference designator), non la posizione interna al componente stesso. Per quanto alcune MDF riportino la distribuzione interna dei materiali (es. incapsulamento, terminali, die), questa distinzione non è tecnicamente rilevante ai fini del recupero — non è possibile separare elementi così intimamente connessi dentro un singolo componente (es. resistore, microprocessore). Per ciascun elemento/materiale si riporterà quindi il suo totale presente in ogni singolo componente.

**Restrizione di scopo — Fase 1: soli componenti C1.** Questa fase si concentra esclusivamente sui **componenti elettrici/elettronici primari** (C1) come quelli presenti su PCB. Questi sono componenti nella loro forma funzionale minima, non ulteriormente semplificabili/smontabili senza perdere le loro caratteristiche. Grandi elettrodomestici, assistenza al disassemblaggio, smistamento materiali e calcolo valori di mercato sono fuori scopo per questa fase.

I file Excel (.xlsx) sono utilizzati esclusivamente come **formato di input** per importare i dati BOM. Tutti i dati persistenti sono memorizzati in un database gestito tramite **Strapi** (headless CMS, https://strapi.io/), accessibile esclusivamente tramite la sua REST API. Il database sottostante è PostgreSQL. È disponibile un **tool di export** CLI per generare report Excel dai dati Strapi (6 fogli: Summary, EEC Categories, Reference Designators, BOM Entries, Devices, Audit Logs).

<a id="sp1.2"></a>

### 1.2 Definizioni e Acronimi

| Acronimo | Definizione                                                      |
| -------- | ---------------------------------------------------------------- |
| AEE      | Apparecchiature Elettriche ed Elettroniche                       |
| RAEE     | Rifiuti da AEE (WEEE)                                            |
| BOM      | Bill of Materials / Distinta Base                                |
| MDF      | Materials Declaration Form / Materials Declaration Sheet         |
| URS      | User Requirements Specification                                  |
| DRS      | Design Requirement Specification                                 |
| OCR      | Riconoscimento Ottico dei Caratteri                              |
| AI       | Intelligenza Artificiale                                         |
| LLM      | Large Language Model                                             |
| CRM      | Materie Prime Critiche (Regolamento UE 2024/1252)                |
| EEC      | Electronic Engineering Components (classificazione 16 categorie) |
| PCB      | Printed Circuit Board                                            |
| SMD      | Surface Mount Device                                             |
| SMT      | Surface-Mount Technology (tecnologia a montaggio superficiale)   |
| THT      | Through-Hole Technology (componenti con piedini passanti)        |
| RoHS     | Restriction of Hazardous Substances (Dir. 2011/65/EU)            |
| CASRN    | Chemical Abstracts Service Registry Number                       |
| MD       | Material Declaration (anche MDF)                                 |
| C1       | Componenti elettrici/elettronici primari                         |
| C2       | Semilavorati / subassemblati                                     |
| C3       | Prodotti finiti pronti per il mercato                            |

<a id="sp1.3"></a>

### 1.3 Riferimenti

- Documento I – Riassunto del Problema e Requisiti Generali (doc1_tropeano.txt)
- Documento II – Riassunto del Progetto e Requisiti Concordati (doc2.txt)
- Progetto Ariadne: Requisiti e Specifiche di Sistema (doc5.md)
- Presentazione Ariadne Digital Path (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)
- Designators EEC -C1 index -X LUCA 2.xlsx
- Scheda STM-Steval Spin3204 BOM (BOM di riferimento per test componenti C1)
- Email "Materiale visto insieme" (26/06/2026)
- Email "Aggiornamento file Designators" (26/06/2026)
- Note di revisione da Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)
- Regolamento UE Materie Prime Critiche (Regolamento UE 2024/1252)
- Standard IEEE/ANSI per Reference Designators
- Scheda STM-Steval Spin3204 - Copia x Luca.xlsx (BOM Excel reale, 17 colonne, riga intestazioni 6)

<a id="p2"></a>

## 2. Descrizione del Sistema

<a id="sp2.1"></a>

### 2.1 Contesto e Motivazioni

L'industria elettronica utilizza oltre 60 materiali, almeno 20 dei quali sono critici e non sostituibili. A livello globale, i paesi industrializzati generano fino a **64 milioni di tonnellate di rifiuti elettronici** all'anno.

Il riciclo tradizionale si basa su triturazione meccanica che permette di recuperare solo **8–10 elementi su 50–60** presenti nei dispositivi. Delle 34 Materie Prime Critiche elencate dall'UE (CRM), 14 presentano **tassi di riciclo a fine vita globali dello 0–5%**.

Il **sistema Ariadne** colma il divario tra i dispositivi RAEE fisici e le informazioni digitali sulla loro composizione interna. Il primo passo — e il focus di questo progetto — è la costruzione di un database strutturato dei materiali presenti nei componenti C1, partendo da BOM reali e dalle corrispondenti Material Declaration Forms.

<a id="sp2.2"></a>

### 2.2 Scopo e Obiettivi di Progetto

**Scopo Fase 1** (questo documento):

- Importare BOM dai produttori (formato Excel) per ottenere un elenco di componenti C1
- Per ogni componente, recuperare la corrispondente **Material Declaration Form (MDF)** dal produttore o distributore
- Estrarre i dati di composizione materiale dalle MDF (tipicamente PDF) e memorizzarli in un database SQL strutturato
- Definire il percorso più efficiente e sicuro: **MDF (PDF) → [opzionale Excel intermedio per validazione] → Strapi API → PostgreSQL**
- Permettere interrogazioni per determinare **quali** materiali, **quanti** (massa) e **dove** (quale componente) si trovano

**Fasi future** (non coperte da questo documento):

- Componenti C2 (semilavorati / subassemblati)
- Componenti C3 (prodotti finiti con Digital Product Passport)
- Riconoscimento tramite computer vision (OpenCV) per identificazione dispositivi
- OCR per PDF scannerizzati (l'estrazione attuale richiede PDF testuali)
- Parsing MDF avanzato con scomposizione strutturata dei materiali
- Assistenza al disassemblaggio per grandi RAEE
- Smistamento materiali (contenitori A-L)
- Calcolo valore di mercato

<a id="sp2.3"></a>

### 2.3 Quadro C1-C2-C3

La piattaforma Ariadne classifica i componenti in tre livelli:

| Livello | Definizione                                                                                                                                           | Esempi                                                                 |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **C1**  | Componenti elettrici/elettronici primari — forma funzionale minima, non ulteriormente semplificabili/smontabili senza perdere le loro caratteristiche | Resistenze, condensatori, transistor, IC, diodi, connettori, cristalli |
| **C2**  | Semilavorati / subassemblati                                                                                                                          | Assemblati PCB, moduli alimentazione, assemblaggi display              |
| **C3**  | Prodotti finiti pronti per il mercato                                                                                                                 | Cellulari, computer, lavatrici                                         |

**La Fase 1 di questo progetto copre solo i componenti C1**, usando BOM reali di PCB come fonte per gli elenchi di componenti.

<a id="sp2.4"></a>

### 2.4 Classificazione Componenti EEC

Il sistema adotta l'indice **EEC (Electronic Engineering Components) a 16 categorie** per classificare le parti elettroniche:

| #   | Categoria                | Sottocategorie                                                                          |
| --- | ------------------------ | --------------------------------------------------------------------------------------- |
| 1   | Cable Assemblies         | Data Transmission, Fiber Optic, RF-Microwave Assemblies                                 |
| 2   | Capacitori               | Alluminio Solido, Ceramico, Film, Vetro, Mica, Semiconduttore, Tantalio                 |
| 3   | Connettori               | Circolari, D-Shaped, PCB, RF Coassiali, Morsettiere                                     |
| 4   | Cristalli e Oscillatori  | Orologi Atomici, Oscillatore a Cristallo, Quarzo                                        |
| 5   | Discreti                 | Diodi, Transistor (BJT, MOSFET, JFET, RF)                                               |
| 6   | Filtri                   | Soppressori Modo Comune, EMI-RFI, Ferrite Beads, SAW                                    |
| 7   | Fusibili e Portafusibili |                                                                                         |
| 8   | Riscaldatori             |                                                                                         |
| 9   | Induttori                | Custom, Potenza, RF                                                                     |
| 10  | Microcircuiti            | Clock/Timing, Comunicazione, Sensori, Memoria, Logica, Processore, Power Management, RF |
| 11  | Relè                     | Ibridi, Latching, Non-Latching, Stato Solido                                            |
| 12  | Resistor                 | Film, Metallo, Reti/Array, Jumper, Avvolto                                              |
| 13  | Interruttori             | Microinterruttori, RF, Scatto, Termostatici, Toggle                                     |
| 14  | Termistori               | NTC, PTC, RTD                                                                           |
| 15  | Trasformatori            | Misura Corrente, Custom, Data Bus, Potenza, Impulsi, RF                                 |
| 16  | Cavi e Fili              | Bassa Frequenza, Altri, RF Coassiali                                                    |

Nota: La categoria EEC è distinta dal reference designator (es. un designator "R" corrisponde sempre alla categoria 12 "Resistors", una "C" alla categoria 2 "Capacitori").

<a id="sp2.5"></a>

### 2.5 Standard Designators

Il sistema supporta i reference designator standard secondo le convenzioni IEEE/ANSI:

| Designator            | Componente                                     |
| --------------------- | ---------------------------------------------- |
| R                     | Resistore                                      |
| C                     | Condensatore                                   |
| L                     | Induttore                                      |
| D                     | Diodo, LED, Zener                              |
| Q                     | Transistor, MOSFET, JFET, IGBT                 |
| U / IC                | Circuito Integrato                             |
| J / P / X / CN / CONN | Connettore                                     |
| Y / XTAL              | Cristallo / Risonatore                         |
| SW / S                | Interruttore                                   |
| F                     | Fusibile                                       |
| FB                    | Ferrite Bead                                   |
| T                     | Trasformatore                                  |
| K / RL                | Relè / Contattore                              |
| M                     | Motore                                         |
| B / BT                | Batteria                                       |
| BZ / LS / SPK / MIC   | Cicalino / Altoparlante / Microfono            |
| ANT                   | Antenna                                        |
| TP                    | Test Point                                     |
| JP / LK               | Jumper / Ponticello                            |
| H / MH / HS           | Hardware (foro, dissipatore)                   |
| RV / VR               | Resistenza Variabile / Trimmer / Potenziometro |
| MOV                   | Varistore a Ossido di Metallo                  |
| TH / RT / NTC / PTC   | Termistore                                     |
| PS / PSU              | Alimentatore                                   |
| REG                   | Regolatore di Tensione                         |
| OSC                   | Oscillatore                                    |
| TB                    | Morsettiera                                    |
| DS / DISP / LCD       | Display                                        |
| GDT                   | Scaricatore a Gas                              |
| TVS                   | Diodo TVS                                      |
| ESD                   | Protezione ESD                                 |
| Z                     | Diodo Zener                                    |

<a id="p3"></a>

## 3. Requisiti

| Priorità | Significato                                                         |
| -------- | ------------------------------------------------------------------- |
| M        | **Obbligatorio:** Requisito essenziale che deve essere implementato |
| D        | **Desiderabile:** Importante ma non strettamente necessario         |
| O        | **Opzionale:** Sarebbe bello avere                                  |
| E        | **Miglioramento Futuro:** Pianificato per versioni successive       |

<a id="sp3.1"></a>

### 3.1 Stakeholder

| Stakeholder                        | Ruolo                                                         |
| ---------------------------------- | ------------------------------------------------------------- |
| Sviluppatore Sistema               | Progetta, sviluppa e mantiene il sistema                      |
| Amministratore Piattaforma Ariadne | Gestisce la piattaforma Ariadne centrale e lo scambio dati    |
| Produttore                         | Fornisce BOM e Material Declaration Forms per i componenti C1 |
| Ricercatore / Analista Dati        | Analizza i dati di composizione materiale dal database        |

<a id="sp3.2"></a>

### 3.2 Requisiti Funzionali

| ID   | Descrizione                                                                                                                                                                                       | Priorità |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| FR1  | Il sistema deve importare file BOM, inizialmente in formato Excel (tramite openpyxl) per la fase di prova e verifica, per ottenere un elenco di componenti C1. Dopo la fase iniziale, l'import diretto da altre fonti potrà sostituire il passaggio Excel — Excel non è mai usato come storage persistente                                     | M        |
| FR2  | Il sistema deve supportare le colonne BOM: Articolo, Quantità, Reference Designator, Valore Parte, Produttore, Codice Ordinamento Produttore, Fornitore 1/2/3, Codice Ordinamento Fornitore 1/2/3 | M        |
| FR3  | Il sistema deve usare l'indice EEC a 16 categorie per classificare ogni componente nella BOM. Il dato EEC va confrontato con quanto riportato nel designator della BOM (se presente nella colonna designator), altrimenti va assegnato automaticamente — deve essere sempre presente                                                                                                      | M        |
| FR4  | Il sistema deve supportare i reference designator standard (IEEE/ANSI, 55+ tipi) per l'identificazione dei componenti                                                                             | M        |
| FR5  | Per ogni componente BOM, il sistema deve memorizzare i dati della Material Declaration Form (MDF): nome materiale (in inglese), CASRN, massa (mg), ed eventuali materiali usati in deroga alla normativa RoHS                                                 | M        |
| FR6  | Il sistema deve distinguere tra elementi materiali e composti (organici/inorganici) nelle dichiarazioni materiali                                                                                 | M        |
| FR7  | Il sistema deve supportare la registrazione di fino a 3 fornitori per componente con i rispettivi numeri di catalogo, per facilitare il reperimento delle MDF                                     | O        |
| FR8  | Il sistema deve memorizzare i metadati del dispositivo/PCB: marca, nome modello, produttore, anno di produzione. I dispositivi vengono creati automaticamente o recuperati durante l'import BOM tramite flag CLI (--brand, --model, --manufacturer, --year), oppure collegati a dispositivi esistenti per nome modello | M        |
| FR9  | Il sistema deve permettere interrogazioni per: **quali** materiali, **quanti** (massa) e **dove** (componente/designator) si trovano in un dispositivo                                            | M        |
| FR10 | Il sistema deve supportare un **export Excel intermedio opzionale** per verifica manuale dei dati MDF estratti dall'AI prima del caricamento nel SQL DB. L'implementazione attuale utilizza DeepSeek AI per l'estrazione BOM da testo PDF, con i dati scritti su SQLite (locale) e opzionalmente sincronizzati su Strapi API (Nota: OCR per PDF scannerizzati e parsing MDF avanzato sono pianificati per fasi successive) | D        |
| FR11 | Il sistema deve essere un'applicazione web accessibile via browser                                                                                                                                | M        |
| FR12 | Il sistema deve integrarsi con la piattaforma dati Ariadne per lo scambio dati e la futura espansione a C2/C3                                                                                     | M        |
| FR13 | Il sistema deve permettere l'inserimento manuale dei dati dei componenti per prodotti senza BOM digitale                                                                                          | D        |
| FR14 | Il sistema deve permettere l'utilizzo di dati di composizione medi/stimati per componenti di cui non si dispone della MDF originale, basati sui dati di componenti simili noti. Questo abiliterà futuri algoritmi predittivi per la stima della composizione di componenti senza MDF diretta | D |

**Nota su AI/LLM, OpenCV, assistenza disassemblaggio, contenitori smistamento e valori di mercato:** DeepSeek AI è attualmente integrato per l'estrazione BOM da PDF testuali. OCR per PDF scannerizzati, computer vision OpenCV, assistenza al disassemblaggio, contenitori smistamento e valori di mercato sono intenzionalmente esclusi dalla Fase 1 e saranno sviluppati in fasi successive della roadmap della piattaforma Ariadne.

<a id="sp3.3"></a>

### 3.3 Requisiti Non Funzionali

| ID   | Descrizione                                                                                                         | Priorità |
| ---- | ------------------------------------------------------------------------------------------------------------------- | -------- |
| NFR1 | Il sistema deve essere facile da usare per inserimento dati e interrogazioni                                        | M        |
| NFR2 | Il sistema deve permettere aggiornamenti di dispositivi, BOM e materiali tramite importazione Excel (openpyxl)        | M        |
| NFR3 | Il sistema deve garantire consistenza e correttezza delle informazioni sui materiali (validazione all'importazione) | M        |
| NFR4 | Il sistema deve memorizzare le masse dei materiali in mg (milligrammi) come unità di misura standard                | M        |
| NFR5 | Il sistema deve essere scalabile per supportare 1000+ modelli di dispositivi e tutte le 16 categorie EEC            | D        |
| NFR6 | Il sistema deve supportare l'integrazione con sistemi esterni, inclusi moduli AI per parsing MDF (API DeepSeek attualmente implementata per estrazione BOM; parsing MDF avanzato per fasi successive) | D        |
| NFR7 | I nomi dei materiali nel DB devono essere in inglese                                                                | M        |

<a id="sp3.4"></a>

### 3.4 Requisiti dei Dati

| ID  | Descrizione                                                                                                                                                                                               | Priorità |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| DR1 | Tutti i dati persistenti devono essere memorizzati in un database gestito tramite Strapi (headless CMS), accessibile esclusivamente tramite la sua REST API. Il database sottostante è PostgreSQL. Excel è usato solo come formato di input e mai come layer di storage                              | M        |
| DR2 | Il sistema deve memorizzare i dati del dispositivo/PCB con: marca, nome modello, produttore, anno di produzione                                                                                           | M        |
| DR3 | Il sistema deve memorizzare i dati BOM con: numero articolo, quantità, reference designator, tipo montaggio (SMT/THT), valore parte, produttore, codice ordinamento produttore, fornitore 1/2/3, codici ordinamento fornitore 1/2/3 | M        |
| DR4 | Il sistema deve memorizzare le dichiarazioni materiali per componente con: nome materiale (inglese), CASRN, massa (mg), classificazione elemento/composto                                                 | M        |
| DR5 | Il sistema deve memorizzare le 16 categorie EEC con sottocategorie per la classificazione dei componenti                                                                                                  | M        |
| DR6 | Il sistema deve memorizzare i reference designator (55+ tipi, IEEE/ANSI) collegati alle categorie EEC                                                                                                     | M        |
| DR7 | Il DB deve permettere interrogazioni per: **quali** materiali, **quanti** (quantità/massa) e **dove** (componente/posizione) si trovano in un dispositivo                                                 | M        |
