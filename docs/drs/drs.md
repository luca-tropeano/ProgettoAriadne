# Ariadne Data-Driven Materials Recovery System

## Project Design Requirement Specification

DIBRIS – University of Genoa. Polytechnic School, Software Engineering Course 80154

<div align='right'> <b> Authors </b> <br> Tropeano Luca </div>

**VERSION : 1.5**

### REVISION HISTORY

| Version | Date       | Author(s) | Notes                                                                                                               |
| ------- | ---------- | --------- | ------------------------------------------------------------------------------------------------------------------ |
| 1.0      | 27/06/2026 | Tropeano  | First complete version based on project data                                                                       |
| 1.1      | 28/06/2026 | Tropeano  | Revision after Rosario's feedback — scope narrowed to C1 only, simplified DB schema, removed future-phase modules  |
| 1.2      | 02/07/2026 | Tropeano  | Rosario feedback revision v2: MountingType, SMT/THT, 'where' clarified, EEC≠designator explained, URS/DRS alignment |
| 1.3      | 02/07/2026 | Tropeano  | Strapi integration: replaced direct SQL Server with Strapi headless CMS + PostgreSQL, updated technology stack and architecture |
| 1.4      | 22/07/2026 | Tropeano  | PDF AI extraction implemented, BOM Import Service updated with device auto-creation and CLI flags, Excel column mapping corrected (17 cols), API token optional, StrapiClient relation payloads fixed, export tool added, 62 xUnit tests passing, bootstrap auto-permissions |
| 1.5      | 29/07/2026 | Tropeano  | Rewrite from C#/.NET to Python 3.11+. BOM processing pipeline: ariadne-py package with openpyxl (Excel), pdfplumber (PDF), DeepSeek AI, SQLite local DB, SFTP upload. pytest test suite. Architecture updated throughout. |

## Table of Contents

- [Ariadne Data-Driven Materials Recovery System](#ariadne-data-driven-materials-recovery-system)
  - [Project Design Requirement Specification](#project-design-requirement-specification)
    - [REVISION HISTORY](#revision-history)
  - [Table of Contents](#table-of-contents)
  - [ 1 Introduction](#-1-introduction)
    - [ 1.1 Purpose and Scope](#-11-purpose-and-scope)
    - [ 1.2 Definitions](#-12-definitions)
    - [ 1.3 Document Overview](#-13-document-overview)
    - [ 1.4 Bibliography](#-14-bibliography)
  - [ 2 Project Description](#-2-project-description)
    - [ 2.1 Project Introduction](#-21-project-introduction)
    - [ 2.2 C1-C2-C3 Framework](#-22-c1-c2-c3-framework)
    - [ 2.3 Technologies Used](#-23-technologies-used)
    - [ 2.4 Assumptions and Constraints](#-24-assumptions-and-constraints)
  - [ 3 System Overview](#-3-system-overview)
    - [ 3.1 System Architecture](#-31-system-architecture)
    - [ 3.2 System Interfaces](#-32-system-interfaces)
    - [ 3.3 System Data](#-33-system-data)
      - [ 3.3.1 System Inputs](#-331-system-inputs)
      - [ 3.3.2 System Outputs](#-332-system-outputs)
       - [ 3.3.3 Database Schema](#db-schema)
    - [BOM Reference: STEVAL-SPIN3204](#bom-reference-steval-spin3204)
  - [ 4 MDF Import and Data Pipeline](#-4-mdf-import-and-data-pipeline)
    - [ 4.1 BOM Import Flow](#-41-bom-import-flow)
    - [ 4.2 MDF Processing and Verification](#-42-mdf-processing-and-verification)
    - [ 4.3 Query Examples](#-43-query-examples)
    - [ 5 Strapi Collection Types Design](#-5-strapi-collection-types-design)
    - [ 6 BOM Import Service Design](#-6-bom-import-service-design)

## <a id="intro"></a> 1 Introduction

<details>
    <summary> The project specification document reflects the design and provides guidance for implementers and developers. </summary>
    Through this document, designers communicate the product design to which implementers or developers must adhere. The project specification must indicate how the design satisfies the requirements.
</details>

### <a id="purpose"></a> 1.1 Purpose and Scope

<details>
    <summary> The purpose of this section is to describe the goal of the document and the target audience </summary>
    <p>This document defines the project specifications for the <b>Ariadne Data-Driven Materials Recovery System</b> (Italian Patent No. 102019000014451, European Patent No. EP4010822). It translates the user requirements defined in the URS into a technical design that guides developers and implementers.</p>
    <p><b>Phase 1 Scope:</b> This design covers exclusively <b>C1 components</b> — primary electrical/electronic components predominantly found on PCBs, which in some cases may also appear in other parts of a device (e.g., power indicator LEDs, switches, potentiometers). In this phase, only the many different components that can be found on PCBs will be addressed, leaving other individual cases to subsequent integrations or revisions. The goal is to build a structured SQL database of materials present in these components, starting from BOM import and Material Declaration Form (MDF) processing. Features such as OpenCV recognition, AI/LLM parsing, disassembly assistance, material sorting, and market value calculation are intentionally excluded from this phase and will be addressed in later phases of the Ariadne platform roadmap.</p>
    <p><b>Key architectural decision:</b> All persistent data is stored in a <b>Strapi-managed database</b> (headless CMS, https://strapi.io/). Data access is <b>accessible exclusively via REST API</b> exposed by Strapi. The underlying database is PostgreSQL. Excel files (.xlsx) are used exclusively as an input format for importing BOM data. The Excel template from Roberto Mantello's thesis serves as a logical reference for the schema design, but the final database is structured as Strapi Collection Types and implemented on PostgreSQL.</p>
</details>

### <a id="def"></a> 1.2 Definitions

<details>
    <summary> Acronyms and key terms used in the document </summary>

| Term  | Definition                                                      |
| ----- | ---------------------------------------------------------------- |
| WEEE  | Waste Electrical and Electronic Equipment                        |
| RAEE  | Rifiuti da AEE (WEEE)                                            |
| BOM   | Bill of Materials / Distinta Base                                |
| MDF   | Materials Declaration Form / Materials Declaration Sheet         |
| DRS   | Design Requirement Specification                                 |
| URS   | User Requirements Specification                                  |
| API   | Application Programming Interface                                |
| REST  | Representational State Transfer                                  |
| openpyxl| Python library for reading/writing Excel files                  |
| CRM   | Critical Raw Materials (Reg. EU 2024/1252)                       |
| EEC   | Electronic Engineering Components (16-category classification)   |
| CASRN | Chemical Abstracts Service Registry Number                       |
| LLM   | Large Language Model                                             |
| C1    | Primary electrical/electronic components                         |
| C2    | Semi-finished goods / sub-assemblies                             |
| C3    | Finished products ready for market                               |
| SMD   | Surface Mount Device                                             |
| SMT   | Surface-Mount Technology                                         |
| THT   | Through-Hole Technology (components with through-hole leads)     |
| RoHS  | Restriction of Hazardous Substances (Dir. 2011/65/EU)            |
| OCR   | Optical Character Recognition                                    |

</details>

### <a id="overview"></a> 1.3 Document Overview

<details>
    <summary> Explains how the document is organized </summary>
    <p>Section 2 describes the project context, objectives, technologies, and constraints, including the C1-C2-C3 framework. Section 3 provides a system overview including architecture, interfaces, and the simplified database schema for Phase 1. Section 4 details the BOM import and MDF processing pipeline, including the optional intermediate verification step on Excel.</p>
</details>

### <a id="biblio"></a> 1.4 Bibliography

<details>
    <summary> Reference documents </summary>
    <p>
    • URS – User Requirements Specification (../urs/urs.md)<br>
    • Document I – Problem Summary and General Requirements (doc1_tropeano.txt)<br>
    • Document II – Project Summary and Agreed Requirements (doc2.txt)<br>
    • Ariadne Project: System Requirements and Specifications (doc5.md)<br>
    • Ariadne Digital Path Presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)<br>
    • Designators EEC -C1 index -X LUCA 2.xlsx<br>
    • STM-Steval Spin3204 Board – Reference BOM<br>
    • Email "Materiale visto insieme" (26/06/2026)<br>
    • Email "Aggiornamento file Designators" (26/06/2026)<br>
    • Review notes from Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)<br>
    • EU Critical Raw Materials Regulation (Regulation EU 2024/1252)
    </p>
</details>

## <a id="description"></a> 2 Project Description

### <a id="project-intro"></a> 2.1 Project Introduction

<details>
    <summary> Describes the high-level project objective and the Phase 1 solution </summary>
    <p>The Ariadne system addresses the inefficiency of current WEEE recycling processes. Most facilities rely on mechanical shredding, which can only recover 8–10 elements out of 50–60. The first step toward a solution — and the purpose of this design — is the construction of a <b>structured SQL database of materials present in C1 components</b>.</p>
    <p><b>Phase 1 Approach:</b></p>
    <p>1. Import real PCB BOMs (Excel) to obtain a list of C1 components<br>
    2. For each component, retrieve the Material Declaration Form (MDF) from the manufacturer or distributor<br>
    3. Extract material data (English names, CASRN, mass in mg) from MDFs<br>
    4. Store data in PostgreSQL via Strapi API<br>
    5. The MDF→DB path may optionally include an intermediate Excel step for manual verification of AI-extracted data</p>
    <p><b>Key architectural decision:</b> The system uses **Strapi** (headless CMS) with PostgreSQL as the database backend. The Excel template from Roberto Mantello's thesis provides a logical trace for the schema, but the final database is structured as Strapi Collection Types and more normalized — in line with the requirement: <i>"Questa è una traccia per l'organizzazione del DB che sarà più strutturato e più capiente."</i> Data is accessed exclusively via Strapi REST API.</p>
</details>

### <a id="c-framework"></a> 2.2 C1-C2-C3 Framework

<details>
    <summary> Three-level component classification in the Ariadne platform </summary>
    <p>The Ariadne platform classifies components into three levels. This phase covers only C1.</p>

| Level | Definition                                                                                                                                           | Examples                                                                      |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **C1**  | Primary electrical/electronic components — minimal functional form, cannot be further simplified/disassembled without losing their characteristics | Resistors, capacitors, transistors, ICs, diodes, connectors, crystals, LEDs |
| **C2**  | Semi-finished goods / sub-assemblies — assembled units that can be further disassembled into C1 components                                            | PCB assemblies, power supply modules, display assemblies with housing   |
| **C3**  | Finished products ready for the market — complete devices                                                                                          | Mobile phones, computers, washing machines, coffee machines                              |

<p><b>Phase 1 covers only C1 components.</b> The BOMs used are exclusively from PCBs, which serve as a source / list of C1 components actually used in electronic production. This approach also helps build a software architecture already prepared to interface with other parts of the Ariadne system in future phases.</p>
    <p><b>Note on mounting type:</b> C1 components are distinguished by their mounting technology on the PCB. This information is relevant for subsequent disassembly phases and must be recorded for each component:</p>
    <p>
    • <b>SMT</b> (Surface-Mount Technology) — component soldered onto the board surface. The acronym <b>SMD</b> (Surface-Mount Device) refers to the component itself.<br>
    • <b>THT</b> (Through-Hole Technology) — component with leads passing through holes in the PCB.
    </p>
</details>

### <a id="tech"></a> 2.3 Technologies Used

<details>
    <summary> Overall architecture description and technology stack for Phase 1 </summary>
    <p>The system is built on the following technology stack:</p>

| Layer       | Technology                                                                         |
| ----------- | ---------------------------------------------------------------------------------- |
| Frontend    | React (or other web framework via Strapi API)                                      |
| Backend API | **Strapi** (headless CMS, automatic REST/GraphQL APIs)                             |
| Database    | SQLite (local) / PostgreSQL (via Strapi)                                           |
| BOM Import  | **Python CLI (ariadne-py)** — openpyxl (Excel parsing), pdfplumber (PDF text extraction) → SQLite / Strapi API |
| AI/LLM      | **DeepSeek API** — BOM extraction from PDF text (implemented)                      |
| Testing     | **pytest** — unit tests covering BOM import, PDF extraction, designator validation |
| Export Tool | **Ariadne Export** — CLI tool to export database to Excel (openpyxl)               |
| OCR         | Future: document recognition for scanned PDFs (subsequent phase)                    |
| Hosting     | Any Python-capable server (Linux/Windows) + Strapi server (if used)                |
   
<p><b>Technologies explicitly excluded from Phase 1:</b> OpenCV (computer vision), OCR for scanned PDFs. These will be introduced in subsequent phases.</p>
</details>

### <a id="constraints"></a> 2.4 Assumptions and Constraints

<details>
    <summary> Boundaries and assumptions that limit design choices </summary>
    <p>
    • BOM data is provided by manufacturers in Excel format with columns: Item, Quantity, Reference Designator, Part Value, Manufacturer, Manufacturer Order Code, Supplier 1/2/3, Supplier 1/2/3 Order Code<br>
    • Excel is used <b>only as an input format</b> — all data is stored in a Strapi-managed database (PostgreSQL), accessible exclusively via REST API<br>
    • The Excel template from the thesis is a <b>logical trace</b> for schema design; the final DB is structured as Strapi Collection Types and more normalized<br>
    • Material Declaration Forms (MDFs) are typically in PDF format and contain substances identified by CASRN<br>
    • Material names in the DB are in English<br>
    • The standard mass unit is the milligram (mg)<br>
    • The system operates on C1 components only (PCB-level components) in Phase 1<br>
    • Development is in Python 3.11+<br>
    • Reference designators follow the IEEE/ANSI standard but must handle specific CAD variants<br>
    • The EEC category is distinct from the reference designator: a reference designator (e.g., "R") identifies the component type (resistor), while the EEC category (e.g., 12 "Resistors") defines its product classification. Multiple designators may belong to the same EEC category. This distinction is necessary because the BOM provides the designator, but the system must be able to classify and group components by EEC category for materials analysis purposes.<br>
    • For each component, the mounting type must be recorded: SMT (Surface-Mount Technology, component soldered onto the PCB surface) or THT (Through-Hole Technology, component with leads passing through holes in the PCB). This information is relevant for subsequent disassembly and processing phases.
    </p>
</details>

## <a id="system-overview"></a> 3 System Overview

<details>
    <summary> High-level description of system structure and behavior </summary>
    <p>The Ariadne system (Phase 1) is a data management web platform focused on BOM import, Material Declaration Form processing, and material composition data storage in a structured SQL database. The system answers <b>which, how many, and where</b> materials are located in the C1 components of a device.</p>
    <p><b>Note on 'WHERE':</b> At the C1 component level, 'where' indicates <b>in which component</b> (which BOM row, identified by the reference designator) a given material is found, not the internal position within the component itself. Although some MDFs report the internal material distribution within a single component (e.g., encapsulation, terminals, die), this distinction is not technically relevant for recovery purposes — it is not possible to separate elements so intimately connected within a single component (e.g., resistor, microprocessor). For each element/material, the total present in each individual component will therefore be reported.</p>
</details>

### <a id="architecture"></a> 3.1 System Architecture

<details>
    <summary> System architecture description and diagram </summary>
    <p>The system follows a three-tier architecture:</p>
    <pre>
[Web Client] ↔ [API Gateway] ↔ [BOM/MDF Service]
                                 ├── [SQL Database]
                                 └── [Audit Logger (basic)]

Data Pipeline:
  BOM Excel → [openpyxl Parser] → SQLite / Strapi API → PostgreSQL (component list)
  MDF PDF → [pdfplumber Text Extraction] → [DeepSeek AI API] → JSON → SQLite / Strapi API → PostgreSQL (materials)
  MDF PDF → [Manual Entry via UI] → Strapi API POST → PostgreSQL (materials)
    </pre>
    <p>The system uses a Python CLI pipeline (ariadne-py) for BOM import. Data is stored locally in SQLite and optionally synced to Strapi API + PostgreSQL when configured. The MDF pipeline supports both manual entry and (in the future) AI-assisted extraction with an optional intermediate Excel step for data verification.</p>

</details>

### <a id="interfaces"></a> 3.2 System Interfaces

<details>
    <summary> External interfaces and interaction points </summary>
    <p>
    • <b>User Interface:</b> Web UI accessible via browser for data entry, import, and queries<br>
    • <b>File Import:</b> BOM Excel upload via openpyxl; MDF PDF upload (for AI processing via pdfplumber + DeepSeek)<br>
    • <b>API Interface:</b> REST endpoints for device management, BOM import, material data entry, queries<br>
    • <b>Database Interface:</b> Strapi REST APIs (automatic CRUD) for persistent storage on PostgreSQL<br>
    • <b>Excel Export (optional):</b> Intermediate export for manual verification of MDF data before committing to DB<br>
    • <b>Database Export (CLI):</b> StrapiExport tool generates 6-sheet Excel from Strapi API (Summary, EEC Categories, Reference Designators, BOM Entries, Devices, Audit Logs)
    </p>
</details>

### <a id="data"></a> 3.3 System Data

<details>
    <summary> Data model overview and data flow </summary>
    <p>The system manages: device/PCB catalog, BOM data for C1 components, material declarations with substances identified by CASRN, EEC categories, and reference designators — all stored as Strapi Collection Types on PostgreSQL, accessible via REST API. Data flows from BOM import through component identification to MDF retrieval and material data storage.</p>
</details>

#### <a id="inputs"></a> 3.3.1 System Inputs

<details>
    <summary> Types of data the system receives </summary>
    <p>
    • BOM Excel files (columns: Item, Quantity, Reference Designator, Part Value, Manufacturer, Manufacturer Order Code, Supplier 1, Supplier 1 Order Code, Supplier 2, Supplier 2 Order Code, Supplier 3, Supplier 3 Order Code) — parsed via openpyxl, stored in SQLite / PostgreSQL; Excel is never used as persistent storage<br>
    • Device metadata: brand, model name, manufacturer, year of production<br>
    • Material Declaration Form (MDF) data: material name (English), CASRN, mass (mg), element/compound classification<br>
    • MDF data can be entered: (a) manually via web UI, (b) via AI extraction with optional intermediate Excel verification<br>
    • Distributor catalog numbers (Supplier 1/2/3) for MDF sourcing path tracking
    </p>
</details>

#### <a id="outputs"></a> 3.3.2 System Outputs

<details>
    <summary> Types of data the system produces </summary>
    <p>
    • Query results: which materials, how many (total mass and per-component mass), where (which component/designator) in a device<br>
    • Material composition reports per device/PCB<br>
    • Optional: intermediate Excel export for MDF data verification before committing to DB<br>
    • Basic audit log for data entry operations
    </p>
</details>

#### <a id="db-schema"></a> 3.3.3 Database Schema

The following schema defines the Strapi Collection Types for Phase 1: C1 component data storage. Collection Types for disassembly, sorting, market values, and distributor management are excluded from this phase. Data access is via Strapi REST API.

**PCB / Device**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| DeviceId | int (PK, IDENTITY) | Primary key | 1 |
| Brand | nvarchar(100) | Device brand | STMicroelectronics |
| ModelName | nvarchar(200) | Model name | STEVAL-SPIN3204 |
| Manufacturer | nvarchar(200) | Manufacturer name | STMICROELECTRONICS |
| YearOfProduction | int | Year of production | 2021 |
| Notes | nvarchar(500) | Additional notes | Rev 211 |

**BOMEntry**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| BOMEntryId | int (PK, IDENTITY) | Primary key | 1 |
| DeviceId | int (FK) | Reference to PCB/Device | 1 |
| ItemNumber | int | BOM row number | 1 |
| Quantity | int | Component quantity | 14 |
| ReferenceDesignator | nvarchar(500) | Designators (comma-separated) | C1,C5,C7,C8,C9,C11 |
| MountingType | nvarchar(10) | Mounting type: SMT, THT | SMT |
| PartValue | nvarchar(100) | Component value | 100 nF |
| Manufacturer | nvarchar(200) | Component manufacturer | KEMET |
| ManufacturerOrderCode | nvarchar(200) | Manufacturer order code | C0603C104K5RACTU |
| Supplier1 | nvarchar(100) | First supplier | DIGIKEY |
| Supplier1OrderCode | nvarchar(200) | Supplier 1 catalog number | PCE3820CT-ND |
| Supplier2 | nvarchar(100) | Second supplier | MOUSER |
| Supplier2OrderCode | nvarchar(200) | Supplier 2 catalog number | 12345 |
| Supplier3 | nvarchar(100) | Third supplier | FARNELL |
| Supplier3OrderCode | nvarchar(200) | Supplier 3 catalog number | 67890 |
| DesignatorCode | nvarchar(10) | Designator code (R, C, U, Q, D...) | C |
| EEC_CategoryId | int (FK) | EEC category (1-16) | 2 |
| Notes | nvarchar(500) | Additional notes | Appro ADEX |

**ComponentMaterial**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| ComponentMaterialId | int (PK, IDENTITY) | Primary key | 1 |
| BOMEntryId | int (FK) | Reference to BOMEntry | 1 |
| MaterialId | int (FK) | Reference to Material | 5 |
| Mass_mg | decimal(12,4) | Mass in mg | 12.5000 |
| Note | nvarchar(500) | Note (alloy, alternative CASRN) | Wire termination |
| SourceMDF | nvarchar(500) | Source MDF filename | MDF_KEMET_C0603.pdf |

**Material**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| MaterialId | int (PK, IDENTITY) | Primary key | 1 |
| MaterialName | nvarchar(200) | Material name (English) | Copper |
| CASRN | nvarchar(20) | CAS Registry Number | 7440-50-8 |
| Category | nvarchar(20) | 'element' or 'compound' | element |

**ReferenceDesignator**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| DesignatorCode | nvarchar(10) (PK) | Designator code | R |
| Name | nvarchar(100) | Component type name | Resistor |
| Description | nvarchar(500) | Full description | Resistor |
| EEC_CategoryId | int (FK) | Corresponding EEC category | 12 |

**EEC_Category**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| CategoryId | int (PK) | Category number (1-16) | 12 |
| Name | nvarchar(100) | Category name | Resistors |
| Subcategories | nvarchar(max) | JSON subcategory list | ["Film","Metal Foil","Network Arrays","Jumper","Wire Wound"] |

**AuditLog**
| Column | Type | Description | Example |
|---------|------|-------------|---------|
| LogId | int (PK, IDENTITY) | Primary key | 1 |
| Timestamp | datetime | Event timestamp | 2026-06-28 10:30:00 |
| UserId | nvarchar(100) | User identifier | luca.tropeano |
| DeviceId | int (FK) | Reference to Device | 1 |
| Action | nvarchar(200) | Action performed | BOM_IMPORT |
| Details | nvarchar(max) | Additional details | 74 components imported |

### BOM Reference: STEVAL-SPIN3204

| Item | Qty | Reference                                        | Part Value      | Package        | Manufacturer       | Mounting |
| ---- | --- | ------------------------------------------------ | --------------- | -------------- | ------------------ | -------- |
| 1    | 14  | C1,C5,C7,C8,C9,C11,C20,C26,C27,C28,C29,C33,C34,C37 | 100 nF         | 0603           | KEMET              | SMT      |
| 2    | 1   | C2                                               | 22 uF           | L8.3_W8.3_H9.5 | PANASONIC          | SMT      |
| 21   | 1   | D1                                               | STPS0560Z       | SOD123         | STMICROELECTRONICS | SMT      |
| 22   | 7   | D2,D9,D10,D11,D12,D13,D14                        | BAT30KFILM      | SOD523         | STMICROELECTRONICS | SMT      |
| 36   | 1   | LD1                                              | RED-GREEN       | PLCC4          | AVAGO              | SMT      |
| 37   | 1   | L1                                               | 22uH            | L3_W3_H1.5     | BOURNS             | SMT      |
| 40   | 6   | Q1-Q6                                            | N-MOS STD140N6F7| DPAK           | STMICROELECTRONICS | SMT      |
| 41   | 1   | Q7                                               | NPN BC847BLT1G  | SOT23          | ON SEMICONDUCTOR   | SMT      |
| 66   | 3   | SW1,SW2,SW3                                      | 430483025816    | L6.2_W6.2_H2.5 | WURTH ELEKTRONIK   | SMT      |
| 70   | 1   | U1                                               | STSPIN32F0B     | VFQFPN48       | STMICROELECTRONICS | SMT      |
| 73   | 1   | U4                                               | STM32F103CBT6   | LQFP48         | STMICROELECTRONICS | SMT      |
| 74   | 1   | X1                                               | 8MHz            | L3.2_W2.5      | NDK                | SMT      |

**Totals:** 199 components, 74 unique types (C1 components only) — all surface-mount (SMT) in this BOM

## <a id="mdf-pipeline"></a> 4 MDF Import and Data Pipeline

### <a id="bom-import"></a> 4.1 BOM Import Flow

<details>
    <summary> Workflow for importing BOM data from files (initially Excel for the trial phase) </summary>
    <p><b>Step 1:</b> The user uploads the BOM file (initially in Excel format for the trial phase, via the web interface)<br>
    <b>Step 2:</b> BOMService parses the file via EPPlus and validates the column structure<br>
    <b>Step 3:</b> Each component is classified:<br>
     - DesignatorValidator checks the reference designator (R, C, U, Q, D, etc.)<br>
     - EECClassifier maps the designator to the corresponding EEC category (1-16)<br>
    <b>Step 4:</b> Device and BOMEntry entities are created/updated in Strapi via REST API<br>
    <b>Step 5:</b> Validation report returned to the user (success count, warnings, unknown designators)</p>
</details>

### <a id="mdf-processing"></a> 4.2 MDF Processing and Verification

<details>
    <summary> The critical path: from Material Declaration Form to PostgreSQL (via Strapi) </summary>
    <p>This is the system's critical path. Two approaches are supported:</p>

    <p><b>Approach A — Manual Entry:</b><br>
    (1) The operator retrieves the MDF PDF from the manufacturer or distributor website<br>
    (2) Reads the material data from the PDF manually<br>
    (3) Enters material name (English), CASRN, mass (mg) via web UI<br>
    (4) The system validates the CASRN format and stores data in PostgreSQL (via Strapi)</p>
    
    <p><b>Approach B — AI-Assisted Extraction (future):</b><br>
    (1) AI extracts text from the MDF PDF via LLM API<br>
    (2) Returns structured JSON with material data<br>
    (3) JSON is parsed and validated<br>
    (4) Data is written to PostgreSQL via Strapi API</p>
    
    <p><b>Approach C — Direct AI to PostgreSQL (via Strapi) (future):</b><br>
    (1) AI extracts and validates data automatically with higher accuracy models<br>
    (2) Data is written directly to PostgreSQL (via Strapi)<br>
    (3) Requires a mature AI model with high accuracy — planned for subsequent phases</p>

</details>

### <a id="queries"></a> 4.3 Query Examples

<details>
    <summary> Key SQL queries for the "which, how many, where" requirement </summary>

    <p><b>Which materials are in a device?</b></p>
    <pre>SELECT DISTINCT m.MaterialName, m.CASRN, m.Category

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'</pre>

    <p><b>How much (mass) of each material?</b></p>
    <pre>SELECT m.MaterialName, SUM(cm.Mass_mg) AS TotalMass_mg

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'
GROUP BY m.MaterialName
ORDER BY TotalMass_mg DESC</pre>

    <p><b>Where (which component) is a specific material found?</b></p>
    <pre>SELECT b.ReferenceDesignator, b.PartValue, b.Manufacturer, cm.Mass_mg

FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204' AND m.CASRN = '7440-50-8'</pre>

</details>

## <a name="strapi-design"></a> 5 Strapi Collection Types Design

<details>
    <summary> Detailed specification of Strapi Collection Types for implementation </summary>

### 5.1 Device

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| brand | Text | required, minLength(1) | Device brand |
| modelName | Text | required, unique | Model name (unique identifier) |
| manufacturer | Text | required | Manufacturer name |
| yearOfProduction | Integer | required, min(1900), max(2030) | Production year |
| notes | RichText | optional | Free notes |

**Permissions:** Full CRUD for Admin and API Key; read-only for Public (if needed).

### 5.2 BOMEntry

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| itemNumber | Integer | required | Line item number from BOM |
| quantity | Integer | required, min(1) | Component quantity |
| referenceDesignator | Text | required | Comma-separated designators |
| mountingType | Enumeration | required, enum: SMT, THT | Mounting type |
| partValue | Text | optional | Component value (e.g. 100 nF) |
| manufacturer | Text | optional | Component manufacturer |
| manufacturerOrderCode | Text | optional | Manufacturer ordering code |
| supplier1 | Text | optional | First supplier |
| supplier1OrderCode | Text | optional | Supplier 1 catalog no. |
| supplier2 | Text | optional | Second supplier |
| supplier2OrderCode | Text | optional | Supplier 2 catalog no. |
| supplier3 | Text | optional | Third supplier |
| supplier3OrderCode | Text | optional | Supplier 3 catalog no. |
| designatorCode | Text | optional | Designator code (R, C, U...) |
| notes | RichText | optional | Additional notes |

**Relations:**
- device (manyToOne → Device) — required
- eecCategory (manyToOne → EEC_Category) — required
- componentMaterials (oneToMany → ComponentMaterial)

**Permissions:** create/update via API Key (BOM import), read via Public API (queries).

### 5.3 ComponentMaterial

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| massMg | Decimal | required, min(0) | Mass in mg |
| note | Text | optional | Alloy, alt CASRN |
| sourceMdf | Text | optional | Source MDF filename |

**Relations:**
- bomEntry (manyToOne → BOMEntry) — required
- material (manyToOne → Material) — required

**Permissions:** create/update via API Key (MDF entry), read Public.

### 5.4 Material

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| materialName | Text | required, unique | Material name (always in English) |
| casrn | Text | optional, unique | CAS Registry Number (format: xxx-yy-z) |
| category | Enumeration | required, enum: element, compound | Classification |

**CASRN validation:** Format `xxx-yy-z` where x=2-7 digits, y=2 digits, z=1 check digit.

**Permissions:** create/update via API Key, read Public.

### 5.5 ReferenceDesignator

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| designatorCode | UID | required, unique | Designator code (R, C, U...) |
| name | Text | required | Name (Resistor, Capacitor...) |
| description | Text | optional | Full description |

**Relations:**
- eecCategory (manyToOne → EEC_Category) — required

### 5.6 EEC_Category

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| categoryId | Integer | required, unique, min(1), max(16) | Category number 1-16 |
| name | Text | required | Category name |
| subcategories | JSON | optional | List of subcategories |

**Relations:**
- referenceDesignators (oneToMany → ReferenceDesignator)
- bomEntries (oneToMany → BOMEntry)

### 5.7 AuditLog

| Field | Strapi Type | Constraints | Notes |
|-------|------------|-------------|-------|
| timestamp | DateTime | required | Event timestamp |
| userId | Text | required | User identifier |
| action | Text | required | Action (e.g. BOM_IMPORT, MDF_INSERT) |
| details | RichText | optional | Additional details |

**Relations:**
- device (manyToOne → Device) — required

**Permissions:** write-only via backend, read Admin.

### 5.8 Permission Summary

| Role | Accessible Collection Types | Operations |
|------|---------------------------|------------|
| Public API (anonymous) | Device, BOMEntry, ComponentMaterial, Material, ReferenceDesignator, EEC_Category, AuditLog | Full CRUD (all operations) |
| API Key (BOM import) | Device, BOMEntry, ComponentMaterial, Material, EEC_Category | POST, PUT (data import) |
| Admin (Strapi admin UI) | All | Full CRUD, permission management |

**Note:** API token is optional — the Public role has full CRUD permissions configured automatically by the bootstrap script (`src/index.ts`). When the API token is empty or starts with `<`, the `StrapiClient` skips the `Authorization` header and relies on Public role permissions.

</details>

## <a name="bom-import-design"></a> 6 BOM Processing Pipeline Design (Python)

<details>
    <summary> Specification of the Python BOM processing pipeline (Excel via openpyxl + PDF via DeepSeek AI) → SQLite / Strapi API </summary>

### 6.1 Pipeline Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────┐
│ BOM Excel   │────▶│ Orchestrator     │────▶│ Database    │────▶│ SQLite /     │
│ (.xlsx)     │     │ (Python)         │     │ (SQLite)    │     │ Strapi API   │
└─────────────┘     └──────────────────┘     └─────────────┘     └──────┬───────┘
                           │                                            │
┌─────────────┐            │                                            ▼
│ MDF PDF     │──▶pdfplumber│ DeepSeek API ──▶ JSON parse               │
│ (.pdf)      │   Extract  │                BOMEntry (Pydantic)         │
└─────────────┘            │                                            ▼
                     ┌──────────────┐                           ┌──────────────┐
                     │ Validation   │                           │ SQLite DB    │
                     │ Designator   │                           │ (local) /    │
                     │ EEC Category │                           │ PostgreSQL   │
                     └──────────────┘                           └──────────────┘
```

### 6.2 Main Modules

**main.py** — CLI entry point (click):
- `ariadne process <file> [--brand] [--model] [--manufacturer] [--year]` — process BOM file
- `ariadne stats` — display database statistics
- Auto-detects file format (.xlsx / .pdf) from extension
- Creates a `Device` pydantic model from CLI flags and dispatches via `Orchestrator`

**Orchestrator** — process coordinator (ariadne/orchestrator.py):
- `process_file(file_path, device)` → `ImportResult` — dispatches to Excel or PDF flow
- `_process_excel(file_path, device)` — calls `parse_excel_bom()` (openpyxl), then `_import_entries()`
- `_process_pdf(file_path, device)` — calls `extract_text_from_pdf()` (pdfplumber), then `DeepSeekClient.extract_bom()`, then `_import_entries()`
- `_import_entries(entries, device)` — shared logic: creates/retrieves device in SQLite, inserts BOM entries

**excel_parser.py** — Excel BOM parsing:
- `parse_excel_bom(file_path)` → `list[BOMEntry]`
- Uses openpyxl for reading `.xlsx` files
- Header row 6, 17-column mapping, auto-detects SMT/THT from Package column

**pdf_extractor.py** — PDF text extraction:
- `extract_text_from_pdf(pdf_path)` → `str`
- `extract_text_from_pdf_stream(stream)` → `str`
- Uses pdfplumber for native PDF text extraction
- Returns page-separated text (does not handle scanned/image PDFs)

**ai_client.py (DeepSeekClient)** — DeepSeek API integration:
- `extract_bom(text, system_prompt)` → `list[BOMEntry]`
- Communicates with DeepSeek API (`/v1/chat/completions`, OpenAI-compatible)
- Returns parsed list of `BOMEntry` pydantic models

**database.py** — SQLite database wrapper:
- `find_or_create_device(device)` → `int` (device_id)
- `insert_bom_entry(device_id, entry)` → `int` (entry_id)
- `get_stats()` → `dict` with device/BOM/material counts
- Uses SQLite via `sqlite3` (standard library)

**models.py** — Pydantic data models:
- `BOMEntry` — Item, Quantity, ReferenceDesignator, PartValue, Package, Manufacturer, etc.
- `Device` — Brand, ModelName, Manufacturer, YearOfProduction
- `ImportResult` — TotalRows, ImportedRows, FailedRows, Success (computed)

**sftp_client.py** — SFTP upload (paramiko):
- `upload_file(local_path, remote_name)` → `str` (remote path)
- Context manager support

**config.py** — Configuration from environment:
- `AppConfig` → `DeepSeekConfig`, `StrapiConfig`, `SFTPConfig`, `DatabaseConfig`
- Auto-loads `.env` file via python-dotenv

### 6.3 Execution Flow — Excel

```
1. Load BOM file (.xlsx) via openpyxl
2. Parse header row 6, iterate data rows (min_row=7)
3. For each row with a valid Item number:
   a. Read cell values by column index:
      - Col 1: Item (int)
      - Col 2: Qty (int)
      - Col 3: Reference (string)
      - Col 5: Part/Value (optional)
      - Col 9: Package → detect SMT/THT (DIP/SIP/TO- → THT, else SMT)
      - Col 10: Manufacturer (optional)
      - Col 11: Mfr Order Code (optional)
      - Col 12: Notes (optional)
      - Col 13: Supplier 1 (optional)
      - Col 14: Supplier 1 Order Code (optional)
   b. Build BOMEntry pydantic model
4. Orchestrator._import_entries():
   a. Database.find_or_create_device() → device_id
   b. For each entry: Database.insert_bom_entry(device_id, entry)
5. Return ImportResult
```

### 6.4 Execution Flow — PDF → DeepSeek AI

```
1. pdf_extractor.extract_text_from_pdf(pdf_path) → raw page-separated text
2. DeepSeekClient.extract_bom(text, system_prompt) → list[BOMEntry]
3. Parse DeepSeek JSON response → validated BOMEntry objects
4. Orchestrator._import_entries():
   a. Database.find_or_create_device() → device_id
   b. For each entry: Database.insert_bom_entry(device_id, entry)
5. Return ImportResult
```

### 6.5 Excel → BOMEntry Column Mapping

The real BOM Excel (`Scheda STM-Steval Spin3204 - Copia x Luca.xlsx`) has **17 columns** with header on row 6. Mapping:

| Excel Col | Header | BOMEntry Field | Notes |
|-----------|--------|----------------|-------|
| 1 | Item | item_number | int parse — skips non-numeric rows |
| 2 | Qty | quantity | int parse |
| 3 | Reference | reference_designator | Comma-separated designators |
| 5 | Part/Value | part_value | Component value (e.g. 100 nF) |
| 9 | Package | mounting_type | DIP/SIP/TO- → THT, else SMT |
| 10 | Manufacturer | manufacturer | Component manufacturer |
| 11 | Mfr Order Code | manufacturer_order_code | String (int cells auto-converted) |
| 12 | Notes | notes | Free-text notes |
| 13 | Supplier | supplier | First supplier |
| 14 | Supplier Code | supplier_order_code | Supplier catalog number |

Columns 4 (Description), 6 (Footprint), 7 (Quantity in stock), 8 (Unit Price), 15-17 (extra supplier data) are present in the file but not mapped.

### 6.6 Database Schema (SQLite)

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

### 6.7 Unit Tests (pytest)

Test suite in `ariadne-py/tests/` using **pytest**:

| Test File | # Tests | What it verifies |
|-----------|---------|------------------|
| test_models.py | 6 | BOMEntry defaults, full model, Device defaults, ImportResult success/failure |
| test_excel_parser.py | 3 | Mounting type detection (SMT, THT, unknown) |
| test_ai_client.py | 3 | DeepSeek response parsing (JSON, markdown-fenced, null fields) |

### 6.8 Pydantic Models

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
    success: bool = True  # computed: success = (failed_rows == 0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
```

### 6.9 CLI Usage

```
ariadne process <file> [--brand X] [--model X] [--manufacturer X] [--year N]

  .xlsx  — import diretto da Excel
  .pdf   — estrazione via DeepSeek AI → DB

Options:
  --brand         Device brand (e.g. STM)
  --model         Device model (e.g. STEVAL-SPIN3204)
  --manufacturer  Device manufacturer
  --year          Year of production
```

```
ariadne stats  — Show database statistics (device/BOM/material counts)
```

</details>

## <a name="export-tool"></a> 7 Database Export Tool

<details>
    <summary> CLI tool for exporting database to Excel (carried over from C# version, to be rewritten in Python) </summary>

### 7.1 Overview

The current export tool (`src/main/Tools/`, C# with EPPlus) exports Strapi data to a formatted Excel workbook with 6 sheets. A Python equivalent using openpyxl is planned.

### 7.2 Generated Sheets

| Sheet | Content |
|-------|---------|
| Summary | Export date, record counts per table, BOM breakdown by designator |
| EEC Categories | All 16 EEC categories with subcategories |
| Reference Designators | All 19 designators with EEC category mapping |
| BOM Entries | Full BOM with all fields, auto-filter enabled |
| Devices | All devices/PCBs |
| Audit Logs | Import operation history |

### 7.3 Architecture (current C# version)

- Uses `HttpClient` to fetch all data from Strapi REST API with pagination
- Uses EPPlus to generate Excel with formatted headers (blue background, white text)
- Outputs to `exports/StrapiExport_YYYYMMDD_HHmmss.xlsx`
- Auto-opens the generated file on completion

</details>
