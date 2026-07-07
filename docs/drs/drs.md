# Ariadne Data-driven Materials Recovery System

## Design Requirement Specification Document

DIBRIS – Università di Genova. Scuola Politecnica, Corso di Ingegneria del Software 80154

<div align='right'> <b> Authors </b> <br> Tropeano Luca </div>

### REVISION HISTORY

| Version | Date       | Author(s) | Notes |
| ------- | ---------- | --------- | ----- |
| 1.2     | 02/07/2026 | Tropeano  | Revision after Rosario feedback v2: MountingType, SMT/THT, 'where' clarified, EEC≠designator explained, URS/DRS alignment |
| 1.1     | 28/06/2026 | Tropeano  | Revision after Rosario feedback — scope focused on C1 components only, simplified DB schema, removed future-phase modules |
| 1.0     | 27/06/2026 | Tropeano  | First complete version based on project data |
| 1.1     | 28/06/2026 | Tropeano  | Revision after Rosario feedback — scope focused on C1 components only, simplified DB schema, removed future-phase modules |

## Table of Content

1. [Introduction](#intro)
   1. [Purpose and Scope](#purpose)
   2. [Definitions](#def)
   3. [Document Overview](#overview)
   4. [Bibliography](#biblio)
2. [Project Description](#description)
   1. [Project Introduction](#project-intro)
   2. [C1-C2-C3 Framework](#c-framework)
   3. [Technologies used](#tech)
   4. [Assumptions and Constraints](#constraints)
3. [System Overview](#system-overview)
   1. [System Architecture](#architecture)
   2. [System Interfaces](#interfaces)
   3. [System Data](#data)
      1. [System Inputs](#inputs)
      2. [System Outputs](#outputs)
      3. [Database Schema](#db-schema)
4. [MDF Import and Data Pipeline](#mdf-pipeline)
   1. [BOM Import Flow](#bom-import)
   2. [MDF Processing and Verification](#mdf-processing)
   3. [Query Examples](#queries)

## <a name="intro"></a> 1 Introduction

<details>
    <summary> The design specification document reflects the design and provides directions to the builders and coders of the product.</summary>
    Through this document, designers communicate the design for the product to which the builders or coders must comply. The design specification should state how the design will meet the requirements.
</details>

### <a name="purpose"></a> 1.1 Purpose and Scope

<details>
    <summary> The goal of this section is to describe the purpose of this document and intended audience </summary>
    <p>This document defines the design specifications for the <b>Ariadne Data-driven Materials Recovery System</b> (Italian Patent No. 102019000014451, European Patent No. EP4010822). It translates the user requirements defined in the URS into a technical design that guides developers and builders.</p>
    <p><b>Phase 1 scope:</b> This design covers exclusively <b>C1 components</b> — primary electrical/electronic components as found on PCBs. The goal is to build a structured SQL database of materials present in these components, starting from BOM import and Material Declaration Form (MDF) processing. Features such as OpenCV recognition, AI/LLM parsing, disassembly guidance, material sorting, and market value calculation are intentionally excluded from this phase and will be addressed in later phases of the Ariadne platform roadmap.</p>
    <p><b>Key architectural decision:</b> All persistent data is stored in a directly implemented SQL Server database. Excel files (.xlsx) are used exclusively as an input format for importing BOM data. The Excel trace from Roberto Mantello's thesis serves as a logical reference for the DB schema design, but the final database is more structured and implemented entirely in SQL Server.</p>
</details>

### <a name="def"></a> 1.2 Definitions

<details>
    <summary> Key acronyms and terms used throughout the document </summary>

| Term | Definition |
| ---- | ---------- |
| AEE  | Apparecchiature Elettriche ed Elettroniche |
| RAEE | Rifiuti da AEE (WEEE) |
| BOM  | Bill of Materials / Distinta Base |
| MDF  | Materials Declaration Form / Materials Declaration Sheet |
| DRS  | Design Requirement Specification |
| URS  | User Requirements Specification |
| API  | Application Programming Interface |
| REST | Representational State Transfer |
| EPPlus | .NET library for reading/writing Excel files |
| CRM  | Critical Raw Materials (EU Regulation 2024/1252) |
| EEC  | Electronic Engineering Components (16-category classification) |
| CASRN | Chemical Abstracts Service Registry Number |
| LLM  | Large Language Model |
| SMD  | Surface Mount Device |
| SMT  | Surface-Mount Technology |
| THT  | Through-Hole Technology |
| RoHS | Restriction of Hazardous Substances (Dir. 2011/65/EU) |
| C1   | Primary electrical/electronic components |
| C2   | Semi-finished products / subassemblies |
| C3   | Finished products ready for market |

</details>

### <a name="overview"></a> 1.3 Document Overview

<details>
    <summary> Explain how is organized the document </summary>
    <p>Section 2 describes the project context, goals, technologies, and constraints, including the C1-C2-C3 framework. Section 3 provides the system overview including architecture, interfaces, and the simplified database schema for Phase 1. Section 4 details the BOM import and MDF processing pipeline, including the optional Excel verification step.</p>
</details>

### <a name="biblio"></a> 1.4 Bibliography

<details>
    <summary> Reference documents </summary>
    <p>
    • URS – User Requirements Specification (URS.md)<br>
    • Document I – Problem Summary and General Requirements (doc1_tropeano.txt)<br>
    • Document II – Project Summary and Agreed Requirements (doc2.txt)<br>
    • Ariadne Project: System Requirements & Specifications (doc5.md)<br>
    • Ariadne Digital Path presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)<br>
    • Designators EEC -C1 index -X LUCA 2.xlsx<br>
    • Scheda STM-Steval Spin3204 - BOM reference<br>
    • Email "Materiale visto insieme" (26/06/2026)<br>
    • Email "Aggiornamento file Designators" (26/06/2026)<br>
    • Revision notes from Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)<br>
    • EU Critical Raw Materials Act (Regulation EU 2024/1252)
    </p>
</details>

## <a name="description"></a> 2 Project Description

### <a name="project-intro"></a> 2.1 Project Introduction

<details>
    <summary> Describe at an high level the goal of the project and the solution for Phase 1 </summary>
    <p>The Ariadne system addresses the inefficiency of current WEEE recycling processes. Most recycling plants rely on mechanical shredding which recovers only 8–10 out of 50–60 elements. The first step toward a solution — and the scope of this design — is building a <b>structured SQL database of materials present in C1 components</b>.</p>
    <p><b>Phase 1 approach:</b></p>
    <p>1. Import real PCB BOMs (Excel) to obtain a list of C1 components<br>
    2. For each component, retrieve the Material Declaration Form (MDF) from the manufacturer or distributor<br>
    3. Extract material data (names in English, CASRN, mass mg) from MDFs<br>
    4. Store the data in a directly implemented SQL Server database<br>
    5. The MDF→DB pipeline may optionally include an intermediate Excel step for manual verification of AI-extracted data</p>
    <p><b>Key architectural decision:</b> The system is built around a directly implemented SQL Server database. The Excel template from Roberto Mantello's thesis provides a logical trace for the schema, but the final database is more structured, normalized, and implemented entirely in SQL Server — in line with the requirement: <i>"Questa è una traccia per l'organizzazione del DB che sarà più strutturato e più capiente."</i></p>
</details>

### <a name="c-framework"></a> 2.2 C1-C2-C3 Framework

<details>
    <summary> Three-level component classification in the Ariadne platform </summary>
    <p>The Ariadne platform classifies components into three levels. This phase covers only C1.</p>

| Level | Definition | Examples |
|-------|-----------|---------|
| **C1** | Primary electrical/electronic components — minimal functional form, cannot be further simplified/disassembled without losing characteristics | Resistors, capacitors, transistors, ICs, diodes, connectors, crystals, LEDs |
| **C2** | Semi-finished products / subassemblies — assembled units that can be further disassembled into C1 components | PCB assemblies, power supply modules, display assemblies with housing |
| **C3** | Finished products ready for market — complete devices | Mobile phones, laptops, washing machines, coffee machines |

<p><b>Phase 1 covers only C1 components.</b> The BOMs used are exclusively from PCBs, serving as a source list of C1 components actually used in real electronic manufacturing. This approach also helps build a software architecture ready to interface with the other parts of the Ariadne system in future phases.</p>
<p><b>Note on mounting type:</b> C1 components are distinguished by their mounting technology on the PCB. This information is relevant for subsequent disassembly phases and must be recorded for each component:</p>
<p>
• <b>SMT</b> (Surface-Mount Technology) — component soldered on the board surface. <b>SMD</b> (Surface-Mount Device) refers to the component itself.<br>
• <b>THT</b> (Through-Hole Technology) — component with leads passing through holes in the PCB.
</p>
</details>

### <a name="tech"></a> 2.3 Technologies used

<details>
    <summary> Description of the overall architecture and technology stack for Phase 1 </summary>
    <p>The system is built on the following technology stack:</p>

| Layer | Technology |
|-------|------------|
| Frontend | ASP.NET Core Blazor / Razor Pages |
| Backend | .NET / C# REST API |
| Database | SQL Server (directly implemented — not Excel) |
| BOM Import | EPPlus (Excel parsing) — Excel is input format only, data stored in SQL Server |
| AI/LLM | Future: MDF parsing from PDF, Doc, Docx (next phase) |
| OCR | Future: document recognition (next phase) |
| Hosting | IIS / Azure App Service |

<p><b>Technologies explicitly excluded from Phase 1:</b> OpenCV (computer vision), AI/LLM for document parsing, OCR. These will be introduced in future phases.</p>
</details>

### <a name="constraints"></a> 2.4 Assumptions and Constraints

<details>
    <summary> Boundaries and assumptions that limit design choices </summary>
    <p>
    • BOM data is provided by manufacturers in Excel format with columns: Item, Quantity, Reference Designator, Part/Value, Manufacturer, Manufacturer Order Code, Supplier 1/2/3, Supplier 1/2/3 Order Code<br>
    • Excel is used <b>only as an input format</b> — all data is stored in a directly implemented SQL Server database<br>
    • The thesis Excel template is a <b>logical trace</b> for schema design; the final DB is more structured and normalized<br>
    • Material Declaration Forms (MDFs) are typically in PDF format and contain CASRN-identified substances<br>
    • Material names in the DB are stored in English<br>
    • Standard mass unit is milligrams (mg)<br>
    • The system operates on C1 components only (PCB-level components) in Phase 1<br>
    • Development is in .NET and C#<br>
    • Reference designators follow IEEE/ANSI standard but must handle CAD-specific variants<br>
    • The EEC category is distinct from the reference designator: a reference designator (e.g. "R") identifies the component type (resistor), while the EEC category (e.g. 12 "Resistors") defines its commodity classification. Multiple designators can belong to the same EEC category. This distinction is necessary because the BOM provides the designator, but the system must classify and group components by EEC category for material analysis purposes.
    • Each component must record its mounting type: SMT (Surface-Mount Technology, component soldered on the PCB surface) or THT (Through-Hole Technology, component with leads through holes in the PCB). This information is relevant for subsequent disassembly and treatment phases.
    </p>
</details>

## <a name="system-overview"></a> 3 System Overview

<details>
    <summary> High-level description of the system's structure and behavior </summary>
    <p>The Ariadne system (Phase 1) is a web-based data management platform focused on importing BOM data, processing Material Declaration Forms, and storing material composition data in a structured SQL database. The system answers <b>quali, quanti e dove</b> (which, how many, where) materials are located in C1 components of a device.</p>
<p><b>Note on "WHERE":</b> At the C1 component level, "where" indicates <b>in which component</b> (which BOM entry, identified by reference designator) a material is found, not the internal position within the component itself. Although some MDFs report material distribution inside a single component (e.g., encapsulation, terminals, die), this distinction is not technically relevant for recovery purposes — it is not possible to separate elements so intimately connected within a single component (e.g., a resistor or microprocessor). For each element/material, the system stores its total mass per individual component.</p>
</details>

### <a name="architecture"></a> 3.1 System Architecture

<details>
    <summary> System architecture description and diagram </summary>
    <p>The system follows a three-tier architecture:</p>
    <pre>
[Web Client] ↔ [API Gateway] ↔ [BOM/MDF Service]
                                 ├── [SQL Database]
                                 └── [Audit Logger (basic)]

Data Pipeline:
  BOM Excel → [EPPlus Parser] → SQL DB (component list)
  MDF PDF → [Manual Entry / AI Extraction] → [Optional Excel Verification] → SQL DB (materials)
    </pre>
    <p>The backend services are stateless REST APIs, with the database handling all persistent state. The MDF pipeline supports both manual data entry and (in the future) AI-assisted extraction with an optional intermediate Excel step for data verification.</p>
</details>

### <a name="interfaces"></a> 3.2 System Interfaces

<details>
    <summary> External interfaces and interaction points </summary>
    <p>
    • <b>User Interface:</b> Web-based UI accessible via browser for data entry, import, and querying<br>
    • <b>File Import:</b> BOM Excel upload via EPPlus; MDF PDF upload (for future AI processing)<br>
    • <b>API Interface:</b> RESTful endpoints for device management, BOM import, material data entry, queries<br>
    • <b>Database Interface:</b> SQL Server connection for persistent data storage<br>
    • <b>Excel Export (optional):</b> Intermediate export for manual MDF data verification before DB commit
    </p>
</details>

### <a name="data"></a> 3.3 System Data

<details>
    <summary> Data model overview and data flow </summary>
    <p>The system manages: device/PCB catalog, BOM data for C1 components, material declarations with CASRN-identified substances, EEC categories, and reference designators — all stored in a directly implemented SQL Server database. Data flows from BOM import through component identification to MDF retrieval and material data storage.</p>
</details>

#### <a name="inputs"></a> 3.3.1 System Inputs

<details>
    <summary> Types of data the system receives </summary>
    <p>
    • BOM Excel files (columns: Item, Quantity, Reference Designator, Part/Value, Manufacturer, Manufacturer Order Code, Supplier 1, Supplier 1 Order Code, Supplier 2, Supplier 2 Order Code, Supplier 3, Supplier 3 Order Code) — parsed via EPPlus, stored in SQL DB; Excel is never used as persistent storage<br>
    • Device metadata: brand, model name, manufacturer, year of production<br>
    • Material Declaration Forms (MDF) data: material name (English), CASRN, mass (mg), element/compound classification<br>
    • MDF data may be entered: (a) manually via UI, (b) via AI extraction with optional Excel intermediate verification<br>
    • Distributor catalog numbers (Supplier 1/2/3) for MDF sourcing path tracking
    </p>
</details>

#### <a name="outputs"></a> 3.3.2 System Outputs

<details>
    <summary> Types of data the system produces </summary>
    <p>
    • Query results: which materials, how many (total mass and per-component mass), where (which component/designator) in a device<br>
    • Material composition reports per device/PCB<br>
    • Optional: intermediate Excel export for MDF data verification before DB commit<br>
    • Basic audit log for data entry operations
    </p>
</details>

#### <a name="db-schema"></a> 3.3.3 Database Schema (SQL Server — Phase 1)

The schema below focuses exclusively on what is needed for Phase 1: C1 component data storage. Tables for disassembly, sorting, market values, and distributor management are excluded from this phase.

**PCB / Device**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| DeviceId | int (PK, IDENTITY) | Primary key | 1 |
| Brand | nvarchar(100) | Device brand | STMicroelectronics |
| ModelName | nvarchar(200) | Device model name | STEVAL-SPIN3204 |
| Manufacturer | nvarchar(200) | Manufacturer name | STMICROELECTRONICS |
| YearOfProduction | int | Production year | 2021 |
| Notes | nvarchar(500) | Additional notes | Rev 211 |

**BOMEntry**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| BOMEntryId | int (PK, IDENTITY) | Primary key | 1 |
| DeviceId | int (FK) | Reference to PCB/Device | 1 |
| ItemNumber | int | Line item in BOM | 1 |
| Quantity | int | Component quantity | 14 |
| ReferenceDesignator | nvarchar(500) | Designators (comma-separated) | C1,C5,C7,C8,C9,C11 |
| MountingType | nvarchar(10) | Mounting type: SMT, THT | SMT |
| PartValue | nvarchar(100) | Component value | 100 nF |
| Manufacturer | nvarchar(200) | Component manufacturer | KEMET |
| ManufacturerOrderCode | nvarchar(200) | Manufacturer ordering code | C0603C104K5RACTU |
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
|--------|------|-------------|---------|
| ComponentMaterialId | int (PK, IDENTITY) | Primary key | 1 |
| BOMEntryId | int (FK) | Reference to BOMEntry | 1 |
| MaterialId | int (FK) | Reference to Material | 5 |
| Mass_mg | decimal(12,4) | Mass in mg | 12.5000 |
| Note | nvarchar(500) | Note (alloy, alt CASRN) | Wire termination |
| SourceMDF | nvarchar(500) | Source filename | MDF_KEMET_C0603.pdf |

**Material**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| MaterialId | int (PK, IDENTITY) | Primary key | 1 |
| MaterialName | nvarchar(200) | Material name (English) | Copper |
| CASRN | nvarchar(20) | CAS Registry Number | 7440-50-8 |
| Category | nvarchar(20) | 'element' or 'compound' | element |

**ReferenceDesignator**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| DesignatorCode | nvarchar(10) (PK) | Designator code | R |
| Name | nvarchar(100) | Component type name | Resistor |
| Description | nvarchar(500) | Full description | Resistenza |
| EEC_CategoryId | int (FK) | Corresponding EEC category | 12 |

**EEC_Category**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| CategoryId | int (PK) | Category number (1-16) | 12 |
| Name | nvarchar(100) | Category name | Resistors |
| Subcategories | nvarchar(max) | JSON list of subcategories | ["Film","Metal Foil","Network Arrays","Jumper","Wire Wound"] |

**AuditLog**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| LogId | int (PK, IDENTITY) | Primary key | 1 |
| Timestamp | datetime | Event time | 2026-06-28 10:30:00 |
| UserId | nvarchar(100) | User identifier | luca.tropeano |
| DeviceId | int (FK) | Reference to Device | 1 |
| Action | nvarchar(200) | Action performed | BOM_IMPORT |
| Details | nvarchar(max) | Additional details | 74 components imported |

### Reference BOM Example: STEVAL-SPIN3204

| Item | Qty | Reference | Part/Value | Package | Manufacturer | Mounting |
|------|-----|-----------|------------|---------|-------------|---------|
| 1 | 14 | C1,C5,C7,C8,C9,C11,C20,C26,C27,C28,C29,C33,C34,C37 | 100 nF | 0603 | KEMET | SMT |
| 2 | 1 | C2 | 22 uF | L8.3_W8.3_H9.5 | PANASONIC | SMT |
| 21 | 1 | D1 | STPS0560Z | SOD123 | STMICROELECTRONICS | SMT |
| 22 | 7 | D2,D9,D10,D11,D12,D13,D14 | BAT30KFILM | SOD523 | STMICROELECTRONICS | SMT |
| 36 | 1 | LD1 | RED-GREEN | PLCC4 | AVAGO | SMT |
| 37 | 1 | L1 | 22uH | L3_W3_H1.5 | BOURNS | SMT |
| 40 | 6 | Q1,Q2,Q3,Q4,Q5,Q6 | N-MOS STD140N6F7 | DPAK | STMICROELECTRONICS | SMT |
| 41 | 1 | Q7 | NPN BC847BLT1G | SOT23 | ON SEMICONDUCTOR | SMT |
| 66 | 3 | SW1,SW2,SW3 | 430483025816 | L6.2_W6.2_H2.5 | WURTH ELEKTRONIK | SMT |
| 70 | 1 | U1 | STSPIN32F0B | VFQFPN48 | STMICROELECTRONICS | SMT |
| 73 | 1 | U4 | STM32F103CBT6 | LQFP48 | STMICROELECTRONICS | SMT |
| 74 | 1 | X1 | 8MHz | L3.2_W2.5 | NDK | SMT |

**Totals:** 199 components, 74 unique types (C1 components only) — all surface-mount (SMT) in this BOM

## <a name="mdf-pipeline"></a> 4 MDF Import and Data Pipeline

### <a name="bom-import"></a> 4.1 BOM Import Flow

<details>
    <summary> Workflow for importing BOM data from Excel </summary>
    <p><b>Step 1:</b> User uploads BOM Excel file via the web interface<br>
    <b>Step 2:</b> BOMService parses the file via EPPlus, validates column structure<br>
    <b>Step 3:</b> Each component is classified:<br>
    &emsp;- DesignatorValidator checks the reference designator (R, C, U, Q, D, etc.)<br>
    &emsp;- EECClassifier maps the designator to the corresponding EEC category (1-16)<br>
    <b>Step 4:</b> Device and BOMEntry entities are created/updated in SQL Server<br>
    <b>Step 5:</b> Validation report returned to user (success count, warnings, unknown designators)</p>
</details>

### <a name="mdf-processing"></a> 4.2 MDF Processing and Verification

<details>
    <summary> The core pipeline: from Material Declaration Form to SQL DB </summary>
    <p>This is the critical path of the system. Two approaches are supported:</p>

    <p><b>Approach A — Manual Entry:</b><br>
    (1) Operator retrieves the MDF PDF from the manufacturer or distributor website<br>
    (2) Reads material data from the PDF manually<br>
    (3) Enters material name (English), CASRN, mass (mg) via the web UI<br>
    (4) System validates CASRN format and stores data in SQL DB</p>

    <p><b>Approach B — AI-Assisted Extraction (with optional Excel verification):</b><br>
    (1) AI extracts material data from the MDF PDF<br>
    (2) Data is written to an intermediate Excel file for human verification<br>
    (3) Operator reviews the Excel file for correctness and completeness<br>
    (4) After approval, data is imported from Excel into SQL DB via EPPlus<br>
    (5) This approach provides a safety check on AI interpretation of complex documents</p>

    <p><b>Approach C — Direct AI to SQL (future):</b><br>
    (1) AI extracts and validates data automatically<br>
    (2) Data is written directly to SQL DB<br>
    (3) Requires mature AI model with high accuracy — planned for later phases</p>
</details>

### <a name="queries"></a> 4.3 Query Examples

<details>
    <summary> Key SQL queries for the "quali, quanti, dove" requirement </summary>

    <p><b>Which materials are in a device?</b></p>
    <pre>SELECT DISTINCT m.MaterialName, m.CASRN, m.Category
FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'</pre>

    <p><b>How many (mass) of each material?</b></p>
    <pre>SELECT m.MaterialName, SUM(cm.Mass_mg) AS TotalMass_mg
FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204'
GROUP BY m.MaterialName
ORDER BY TotalMass_mg DESC</pre>

    <p><b>Where (which component) is a specific material?</b></p>
    <pre>SELECT b.ReferenceDesignator, b.PartValue, b.Manufacturer, cm.Mass_mg
FROM Device d
JOIN BOMEntry b ON d.DeviceId = b.DeviceId
JOIN ComponentMaterial cm ON b.BOMEntryId = cm.BOMEntryId
JOIN Material m ON cm.MaterialId = m.MaterialId
WHERE d.ModelName = 'STEVAL-SPIN3204' AND m.CASRN = '7440-50-8'</pre>
</details>
