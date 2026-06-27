# Ariadne Data-driven Materials Recovery System

## Design Requirement Specification Document

DIBRIS – Università di Genova. Scuola Politecnica, Corso di Ingegneria del Software 80154

<div align='right'> <b> Authors </b> <br> Tropeano Luca </div>

### REVISION HISTORY

| Version | Data | Author(s) | Notes |
| --- | --- | --- | --- |
| 1.0 | 27/06/2026 | Tropeano | First complete version based on project data. |

## Table of Content

1. [Introduction](#intro)
  1. [Purpose and Scope](#purpose)
  2. [Definitions](#def)
  3. [Document Overview](#overview)
  4. [Bibliography](#biblio)
2. [Project Description](#description)
  1. [Project Introduction](#project-intro)
  2. [Technologies used](#tech)
  3. [Assumptions and Constraints](#constraints)
3. [System Overview](#system-overview)
  1. [System Architecture](#architecture)
  2. [System Interfaces](#interfaces)
  3. [System Data](#data)
    1. [System Inputs](#inputs)
    2. [System Outputs](#outputs)
    3. [Database Schema](#db-schema)
4. [System Module 1 – Recognition App](#sys-module-1)
  1. [Structural Diagrams](#sd)
    1. [Class Diagram](#cd)
      1. [Class Description](#cd-description)
    2. [Object Diagram](#od)
    3. [Dynamic Models](#dm)
5. [System Module 2 – Material Declaration App](#sys-module-2)
  1. [Structural Diagrams](#sd2)
    1. [Class Diagram](#cd2)
    2. [Dynamic Models](#dm2)

## 1 Introduction

<details>
    <summary> The design specification document reflects the design and provides directions to the builders and coders of the product.</summary> 
    Through this document, designers communicate the design for the product to which the builders or coders must comply. The design specification should state how the design will meet the requirements.
</details>

### 1.1 Purpose and Scope

<details> 
    <summary> The goal of this section is to describe the purpose of this document and intended audience </summary>
    <p>This document defines the design specifications for the <b>Ariadne Data-driven Materials Recovery System</b> (Italian Patent No. 102019000014451, European Patent No. EP4010822). It translates the user requirements defined in the URS into a technical design that guides developers and builders. The intended audience includes software architects, developers, testers, and project stakeholders involved in the implementation phase.</p>
    <p><b>Key architectural decision:</b> All persistent data is stored in a directly implemented SQL database. Excel files (.xlsx) are used exclusively as an input format for importing BOM and material declaration data into the database. The thesis Excel template by Roberto Mantello serves as a logical trace for the DB schema design, but the final database is more structured, more capacious, and fully implemented in SQL Server — not in Excel.</p>
</details>

### 1.2 Definitions

<details> 
    <summary> Key acronyms and terms used throughout the document </summary>
    <p>This subsection lists the acronyms and terms used in the design specification.</p>

| Term | Definition |
| --- | --- |
| WEEE | Waste Electrical and Electronic Equipment |
| BOM | Bill of Materials |
| DRS | Design Requirement Specification |
| URS | User Requirements Specification |
| OCR | Optical Character Recognition |
| API | Application Programming Interface |
| REST | Representational State Transfer |
| SIFT/ORB | Feature matching algorithms used in computer vision |
| EPPlus | .NET library for reading/writing Excel files |
| CRM | Critical Raw Materials (EU Regulation 2024/1252) |
| EEC | Electronic Engineering Components (16-category classification) |
| CASRN | Chemical Abstracts Service Registry Number |
| LLM | Large Language Model |
| AVI | Automatic Visual Inspection |
| MD  | Material Declaration |

</details>

### 1.3 Document Overview

<details> 
    <summary> Explain how is organized the document </summary>
    <p>Section 2 describes the project context, goals, technologies, and constraints. Section 3 provides the system overview including architecture, interfaces, and data flow with real project data. Sections 4 and 5 detail the two main system modules: the Recognition App and the Material Declaration App, including structural and dynamic models.</p>
</details>

### 1.4 Bibliography

<details> 
    <summary> Reference documents </summary>
    <p>
    • URS – User Requirements Specification (URS.md)<br>
    • Document I – Problem Summary and General Requirements (doc1_tropeano.txt)<br>
    • Document II – Project Summary and Agreed Requirements (doc2.txt)<br>
    • Ariadne Project: System Requirements & Specifications (doc5.md)<br>
    • Ariadne Digital Path presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)<br>
    • Designators EEC -C1 index -X LUCA 2.xlsx (component classification, designators, distributor list)<br>
    • Scheda STM-Steval Spin3204 - BOM reference<br>
    • Email "Materiale visto insieme" (26/06/2026) — requirements for structured DB at Point C1 of Ariadne data flow; thesis Excel as logical trace (the final DB will be more structured and capacious)<br>
    • Email "Aggiornamento file Designators" (26/06/2026) — distributor catalog numbers for MD sourcing<br>
    • Roberto Mantello thesis — Excel template as logical trace for DB schema<br>
    • EU Critical Raw Materials Act (Regulation EU 2024/1252)
    </p>
</details>

## 2 Project Description

### 2.1 Project Introduction

<details> 
    <summary> Describe at an high level what is the goal of the project and a possible solution </summary>
    <p>The Ariadne system addresses the inefficiency of current WEEE recycling processes. Most recycling plants rely on mechanical shredding recovering only 8–10 out of 50–60 elements. The proposed solution is a data-driven software tool that identifies WEEE devices via images or identifiers, retrieves BOM and material data, and provides disassembly guidance to operators. The system consists of two web applications: a Recognition App (computer vision-based device identification) and a Material Declaration App (BOM management, component mapping, and recovery tracking).</p>
    <p><b>Core architectural decision:</b> The system is built around a <b>directly implemented SQL Server database</b>. Excel files are used solely as an input format for importing BOM and Material Declaration data into the DB. The thesis Excel template by Roberto Mantello provides a logical trace for the schema, but the final database is more structured and more capacious — as per the email requirement: <i>"Questa è una traccia per l'organizzazione del DB che sarà più strutturato e più capiente."</i></p>
    <p>The system leverages AI through Large Language Models (LLMs) for processing complex material declaration documents and Computer Vision (OpenCV) for PCB and component recognition. The Ariadne platform processes data from BOM and Material Declaration Forms to enable selection of each component on a PCB based on its material composition.</p>
</details>

### 2.2 Technologies used

<details> 
    <summary> Description of the overall architecture and technology stack </summary>
    <p>The system is built on the following technology stack:</p>

| Layer | Technology |
| --- | --- |
| Frontend | ASP.NET Core Blazor / Razor Pages |
| Backend | .NET / C# REST API |
| Database | SQL Server |
| Computer Vision | OpenCV (OpenCvSharp .NET wrapper) — SIFT/ORB feature matching, Automatic Visual Inspection (AVI) |
| AI/LLM Integration | Large Language Models for material declaration document parsing |
| BOM Import | EPPlus (Excel parsing with support for all 16 EEC categories) — Excel is input format only, data is stored in SQL Server |
| OCR (optional) | Tesseract .NET |
| Hosting | IIS / Azure App Service |
| Barcode/QR | Standard barcode and QR code scanning libraries |

</details>

### 2.3 Assumptions and Constraints

<details> 
    <summary> Boundaries and assumptions that limit design choices </summary>
    <p>
    • BOM data is provided by manufacturers in Excel format with specific column structure (Item, Quantity, Reference, Part/Value, Voltage/Watt/Ampere, Type/TECHNOLOGY, Tolerance, Package, Manufacturer, Ordering Code, Supplier)<br>
    • Excel is used **only as an import format** — all data is stored in a directly implemented SQL Server database<br>
    • The thesis Excel template (Roberto Mantello) is a **logical trace** for schema design; the final DB is more structured and capacious<br>
    • Manuals may be scanned PDFs; OCR may be needed for text extraction<br>
    • Material Declarations use CAS Registry Numbers for chemical identification<br>
    • Standard mass unit is milligrams (mg)<br>
    • Legacy devices without digital BOM require manual data entry<br>
    • The system operates in a plant environment with network connectivity<br>
    • Users have basic technical skills only<br>
    • The system is a decision-support tool, not fully automated — operators make final sorting decisions<br>
    • Development is in .NET and C# as per project requirements<br>
    • Reference designators follow IEEE/ANSI standard but must handle CAD-specific variants
    </p>
</details>

## 3 System Overview

<details> 
    <summary> High-level description of the system's structure and behavior </summary>
    <p>The Ariadne system is a web-based platform composed of two main applications that share a common backend and database. The Recognition App handles device identification via OpenCV and AI, while the Material Declaration App manages BOM data and material recovery tracking. The full Ariadne model includes data flow from manufacturers (Full Material Declaration C1 → Bill Of Materials → Ariadne platform → Digital Product Passport) through to the physical sorting line with A-L color-coded containers.</p>
    <p><b>Database note:</b> The structured DB at point C1 is the heart of the system. It stores all material declarations and enables querying <b>quali, quanti e dove</b> (which, how many, where) materials are located. Excel is never used as a storage layer — only for initial data import.</p>
</details>

### 3.1 System Architecture

<details> 
    <summary> System architecture description and diagram </summary>
    <p>The system follows a three-tier architecture with a web client, an API gateway, and backend services. The main components are:</p>
    <pre>
[Web Client] ↔ [API Gateway] ↔ [Recognition Service]
                                 ├── [BOM Database (SQL Server)]
                                 ├── [Material Declaration Service]
                                 ├── [AI/OpenCV Module]
                                 ├── [LLM Document Parser]
                                 └── [Audit Logger]

Physical Sorting Line Integration:
 Workstation 2 (identification) → 3-4 (rotating disassembly) → 
6-7 (guide panel with monitors) → A-L (color-coded chests)
 </pre>
 <p>The backend services are stateless REST APIs, with the database handling all persistent state. OpenCV runs server-side for image preprocessing and feature matching. LLMs process unstructured material declarations.</p>

</details>

### 3.2 System Interfaces

<details> 
    <summary> External interfaces and interaction points </summary>
    <p>
    • <b>User Interface:</b> Web-based UI accessible via browser on tablets or workstations, with color-coded material selection (A-L chests)<br>
    • <b>Camera Interface:</b> Device camera capture for real-time image acquisition and PCB Automatic Visual Inspection (AVI)<br>
    • <b>File Import:</b> Excel BOM upload via EPPlus; Material Declaration Form upload; PDF manual upload via file storage<br>
    • <b>API Interface:</b> RESTful endpoints for device lookup, BOM retrieval, material declarations, disassembly steps, log access<br>
    • <b>Database Interface:</b> SQL Server connection for persistent data storage of devices, BOMs, components, materials, designators<br>
    • <b>Physical Line Interface:</b> Monitor display for operator guidance (points 6-7), A-L container labeling system
    </p>
</details>

### 3.3 System Data

<details> 
    <summary> Data model overview and data flow </summary>
    <p>The system manages: device catalog, BOM data (199+ components, 74+ types per device), component materials (185+ materials including 95 chemical elements and 91 compounds), reference designators (55+ types), disassembly instructions, material market values (€/t), and audit logs — all stored in a directly implemented SQL database. Data flows from input acquisition through recognition, enrichment, and presentation to the operator.</p>
</details>

#### 3.3.1 System Inputs

<details> 
    <summary> Types of data the system receives </summary>
    <p>
    • Device images (external view and internal PCB photos)<br>
    • Serial numbers (text input)<br>
    • Barcodes or QR codes (scanned from device labels)<br>
    • Excel BOM files from manufacturers (columns: Item, Quantity, Reference, Part/Value, Voltage/Watt/Ampere, Type/TECHNOLOGY, Tolerance, Package, Manufacturer, Ordering Code, Additional Notes, Supplier, Supplier Ordering Code) — **parsed via EPPlus and stored in SQL DB; Excel is never used as persistent storage**<br>
    • Material Declaration Forms with CASRN-identified substances — imported into the structured DB<br>
    • PDF manuals (structured or scanned)<br>
    • Operator manual corrections and sorting feedback<br>
    • Distributor catalog numbers (Arrow, Avnet, Mouser, DigiKey, Farnell, RS, TME, etc.) — for MD sourcing path tracking
    </p>
</details>

#### 3.3.2 System Outputs

<details> 
    <summary> Types of data the system produces </summary>
    <p>
    • Device identification result (model, family, manufacturer, confidence score)<br>
    • Bill of Materials with full component list (reference, value, package, manufacturer)<br>
    • Material breakdown per component: type, CASRN, mass (mg), percentage, element/compound classification<br>
    • Financial value estimation per material type (€/t based on market prices)<br>
    • Step-by-step disassembly instructions with visual aids and color-coded sorting guidance<br>
    • Color-coded material sorting to A-L chests<br>
    • Audit logs with timestamps, users, devices, actions for regulatory compliance<br>
    • Recovery efficiency reports (e.g., "Steels in Linea Mini: AISI430 500€/t, AISI304L 1700€/t, AISI316L 2800€/t")
    </p>
</details>

#### 3.3.3 Database Schema (Directly Implemented SQL Server)

The schema below is derived from the logical trace of the thesis Excel template, but the database is **directly implemented in SQL Server** — not in Excel. The thesis template served as an organizational reference; the final schema is more structured, more normalized, and more capacious, with proper primary keys, foreign keys, and data types.

**Device**
| Column | Type | Description |
|--------|------|-------------|
| DeviceId | int (PK) | Primary key |
| ModelName | nvarchar(200) | Device model name |
| Manufacturer | nvarchar(200) | Manufacturer name |
| ProductFamily | nvarchar(200) | Product family |
| EEC_CategoryId | int (FK) | Reference to 16 EEC categories |
| TotalWeight_mg | decimal | Total device weight in mg |
| TotalComponents | int | Total component count from BOM |

**BOMEntry**
| Column | Type | Description |
|--------|------|-------------|
| BOMEntryId | int (PK) | Primary key |
| DeviceId | int (FK) | Reference to Device |
| ItemNumber | int | Line item number in BOM |
| Quantity | int | Component quantity |
| ReferenceDesignators | nvarchar(500) | Comma-separated designators (e.g., "C1,C5,C7") |
| PartValue | nvarchar(100) | Value (e.g., "100 nF", "39 K") |
| VoltageWattAmpere | nvarchar(100) | Rating |
| Technology | nvarchar(100) | Type (CER, ALU, RES, LED, etc.) |
| Tolerance | decimal | Tolerance percentage |
| Package | nvarchar(100) | Package type (0603, 0805, SOT23, LQFP48, etc.) |
| Manufacturer | nvarchar(200) | Component manufacturer |
| ManufacturerOrderCode | nvarchar(200) | Manufacturer ordering code |
| AdditionalNotes | nvarchar(500) | Notes |
| Supplier | nvarchar(200) | Supplier name |
| SupplierOrderCode | nvarchar(200) | Supplier ordering code |

**ReferenceDesignator**
| Column | Type | Description |
|--------|------|-------------|
| DesignatorId | int (PK) | Primary key |
| Code | nvarchar(10) | Code (R, C, U, Q, D, J, etc.) |
| Name | nvarchar(100) | Component type name |
| Description | nvarchar(500) | Full description |
| Standard | nvarchar(50) | Standard reference (IEEE/ANSI) |

**EEC_Category**
| Column | Type | Description |
|--------|------|-------------|
| CategoryId | int (PK) | Primary key (1-16) |
| Name | nvarchar(100) | Category name |
| Subcategories | nvarchar(max) | JSON list of subcategories |

**Material**
| Column | Type | Description |
|--------|------|-------------|
| MaterialId | int (PK) | Primary key |
| MaterialName | nvarchar(200) | Material name |
| CASRN | nvarchar(20) | CAS Registry Number |
| Category | nvarchar(20) | 'element' or 'compound' |
| MarketValue_eur_per_ton | decimal | Market value in €/t |

**ComponentMaterial**
| Column | Type | Description |
|--------|------|-------------|
| ComponentMaterialId | int (PK) | Primary key |
| BOMEntryId | int (FK) | Reference to BOMEntry |
| MaterialId | int (FK) | Reference to Material |
| Mass_mg | decimal | Mass in milligrams |
| Percentage | decimal | Percentage composition |
| Note | nvarchar(500) | Note (e.g., alloy info, alternative CASRN) |

**DisassemblyStep**
| Column | Type | Description |
|--------|------|-------------|
| StepId | int (PK) | Primary key |
| DeviceId | int (FK) | Reference to Device |
| StepNumber | int | Step order |
| Instruction | nvarchar(max) | Text instruction |
| ImagePath | nvarchar(500) | Path to visual aid image |
| TargetChest | nvarchar(10) | Target sorting chest (A-L) |
| MaterialType | nvarchar(100) | Material type for this step |

**Distributor**
| Column | Type | Description |
|--------|------|-------------|
| DistributorId | int (PK) | Primary key |
| Name | nvarchar(200) | Distributor name |
| Notes | nvarchar(500) | Notes about the distributor |
| Website | nvarchar(200) | Website URL |

**ComponentDistributor**
| Column | Type | Description |
|--------|------|-------------|
| ComponentDistributorId | int (PK) | Primary key |
| BOMEntryId | int (FK) | Reference to BOMEntry |
| DistributorId | int (FK) | Reference to Distributor |
| CatalogNumber | nvarchar(200) | Distributor catalog number |

**AuditLog**
| Column | Type | Description |
|--------|------|-------------|
| LogId | int (PK) | Primary key |
| Timestamp | datetime | Event timestamp |
| UserId | nvarchar(100) | User identifier |
| DeviceId | int (FK) | Reference to Device |
| Action | nvarchar(200) | Action performed |
| Details | nvarchar(max) | Additional details |
| ChestUsed | nvarchar(10) | Target sorting chest (if applicable) |
| MaterialMass_mg | decimal | Mass of sorted material |

### Reference BOM Example: STEVAL-SPIN3204

| Item | Qty | Reference | Part/Value | Package | Manufacturer |
| --- | --- | --- | --- | --- | --- |
| 1   | 14  | C1,C5,C7,C8,C9,C11,C20... | 100 nF | 0603 | KEMET |
| 2   | 1   | C2  | 22 uF | L8.3_W8.3_H9.5 | PANASONIC |
| 3   | 4   | C3,C25,C40,C41 | 220 nF | 0803 | KEMET |
| 10  | 2   | C16,C17 | 220 uF | L13.5_W13.5_H15 | PANASONIC |
| 21  | 1   | D1  | STPS0560Z | SOD123 | STMICROELECTRONICS |
| 22  | 7   | D2,D9-D14 | BAT30KFILM | SOD523 | STMICROELECTRONICS |
| 36  | 1   | LD1 | RED-GREEN | PLCC4 | AVAGO |
| 37  | 1   | L1  | 22uH | L3_W3_H1.5 | BOURNS |
| 40  | 6   | Q1-Q6 | N-MOS STD140N6F7 | DPAK | STMICROELECTRONICS |
| 41  | 1   | Q7  | NPN BC847BLT1G | SOT23 | ON SEMICONDUCTOR |
| 66  | 3   | SW1,SW2,SW3 | 430483025816 | L6.2_W6.2_H2.5 | WURTH ELEKTRONIK |
| 70  | 1   | U1  | STSPIN32F0B | VFQFPN48 | STMICROELECTRONICS |
| 73  | 1   | U4  | STM32F103CBT6 | LQFP48 | STMICROELECTRONICS |
| 74  | 1   | X1  | 8MHz | L3.2_W2.5 | NDK |

**Totals:** 199 components, 74 unique types, ~43.8g total mass

## 4 System Module 1 – Recognition App

<details> 
    <summary> The Recognition App handles device identification through computer vision and AI </summary>
    <p>This module accepts images or identifiers, processes them via OpenCV, matches against the device database, and returns the identified model with confidence. It also handles uncertainty by offering top-K matches and allowing manual override. The module connects to Workstation 2 (identification station) in the physical Ariadne line layout.</p>
</details>

### 4.1 Structural Diagrams

<details> 
    <summary> UML diagrams describing the static structure of the Recognition module </summary>
    <p>The module follows a Service-Repository pattern with clear separation between the API layer, recognition logic, and data access. It supports AI-based smart recognition and uses LLMs for processing unstructured material declarations.</p>
</details>

#### 4.1.1 Class diagram

<details> 
    <summary> Main classes of the Recognition module </summary>
    <p>The core classes include RecognitionController (API endpoint), RecognitionService (business logic), DeviceRepository (data access), OpenCVService (image processing with SIFT/ORB), LLMParserService (for material declaration documents), and domain models: Device, Component, Material, BOMEntry, ReferenceDesignator.</p>
</details>

##### 4.1.1.1 Class Description

<details> 
    <summary> Detailed description of each class in the Recognition module </summary>
    <p>
    • <b>RecognitionController:</b> REST API controller exposing endpoints for image upload, serial lookup, barcode/QR scan, and manual correction feedback<br>
    • <b>RecognitionService:</b> Orchestrates the recognition pipeline: image preprocessing, feature extraction (SIFT/ORB), database matching, confidence scoring, AI/LLM fallback for uncertain matches<br>
    • <b>DeviceRepository:</b> Data access layer for querying the device catalog (1000+ models), BOM data, material declarations, and storing operator feedback<br>
    • <b>OpenCVService:</b> Wraps OpenCV operations (resize, denoise, SIFT/ORB feature matching, contour detection for PCB component identification)<br>
    • <b>LLMParserService:</b> Handles parsing of material declaration documents in various formats using LLMs, extracts material names, CASRN, and quantities<br>
    • <b>Device:</b> Domain entity representing a WEEE device with model name, manufacturer, product family, EEC category, total mass<br>
    • <b>BOMEntry:</b> Domain entity for each line in the BOM with component specifications, manufacturer, suppliers, ordering codes<br>
    • <b>ReferenceDesignator:</b> Domain entity for standard component codes (R, C, U, Q, D, J, etc.)<br>
    • <b>Component:</b> Domain entity for each physical part with position, material composition link<br>
    • <b>Material:</b> Domain entity with material type, CASRN, mass (mg), market value (€/t), element/compound classification
    </p>
</details>

#### 4.1.2 Object diagram

<details> 
    <summary> Example object instances at runtime </summary>
    <p><b>Example: STEVAL-SPIN3204 at runtime</b></p>
    <p>
    Device: "STEVAL-SPIN3204" by STMICROELECTRONICS, total mass 43.8g, 199 components<br>
    → BOMEntry: U4, STM32F103CBT6 (MCU), LQFP48, 1 unit<br>
    → BOMEntry: U1, STSPIN32F0B (Driver), VFQFPN48, 1 unit<br>
    → BOMEntry: 14× capacitors 100nF (C1,C5,C7...), 0603, KEMET<br>
    → BOMEntry: resistors (R1-R75), various values, 0603, YAGEO<br>
    → BOMEntry: 6× N-MOSFET (Q1-Q6), DPAK, STMICROELECTRONICS<br>
    → Material: Copper (CASRN 7440-50-8), Gold (CASRN 7440-57-5), Tin (CASRN 7440-31-5), Silicon, etc.<br>
    → Disassembly steps: 10+ steps with color-coded chest assignments
    </p>
    <p><b>Example: Coffee Machine (from Ariadne presentation)</b></p>
    <p>
    Device: "Linea Mini" coffee machine<br>
    → Component: Steel AISI430, mass 7,398mg, value 500€/t<br>
    → Component: Steel AISI316L, mass 4,334mg, value 2,800€/t<br>
    → Component: Steel AISI304L, mass 3,579mg, value 1,700€/t<br>
    → Component: Zinc plated steel, mass 87.5mg<br>
    → Component: Plastic, various types<br>
    → Total steel mass: 15,455mg (54% of device)
    </p>
</details>

#### 4.2 Dynamic Models

<details> 
    <summary> Sequence and activity diagrams for key recognition workflows </summary>
    <p><b>Recognition Flow (Image-based):</b><br>
    (1) Operator captures device image at Workstation 2 → (2) RecognitionController receives image → (3) RecognitionService calls OpenCVService for preprocessing → (4) SIFT/ORB feature extraction performed → (5) DeviceRepository queried for feature matches → (6) Top-K results returned with confidence scores → (7) Operator confirms or corrects via monitor 6-7 → (8) Feedback stored in database → (9) Device sent to disassembly station 3-4</p>
    <p><b>Recognition Flow (Barcode/QR):</b><br>
    (1) Operator scans barcode/QR at Workstation 2 → (2) RecognitionController receives code → (3) RecognitionService queries DeviceRepository by product code → (4) Device identified → (5) Result displayed on monitor with BOM summary</p>
    <p><b>AI/LLM Document Parsing Flow:</b><br>
    (1) Manufacturer submits Material Declaration Form → (2) LLMParserService processes document via LLM → (3) Material names, CASRNs, quantities extracted → (4) Results validated against existing database → (5) New materials created or existing ones updated → (6) BOM linked to parsed material data</p>
</details>

## 5 System Module 2 – Material Declaration App

<details> 
    <summary> The Material Declaration App manages BOM data, component-material mapping, and recovery tracking </summary>
    <p>This module allows importing BOM Excel files, viewing device component trees with material breakdown, navigating disassembly steps (points 3-4 and 6-7), and tracking sorted materials against recovery targets using the A-L color-coded container system.</p>
</details>

### 5.1 Structural Diagrams

<details> 
    <summary> UML diagrams for the Material Declaration module </summary>
    <p>The module shares domain models with the Recognition module but adds services specific to BOM management (EEC classification, designator validation), disassembly guidance (with A-L chest mapping), material value calculation, and audit logging.</p>
</details>

#### 5.1.1 Class diagram

<details> 
    <summary> Main classes of the Material Declaration module </summary>
    <p>
    • <b>MaterialController:</b> REST API for BOM queries (by device, category, designator), material declarations, disassembly steps, sorting instructions, audit logs<br>
    • <b>BOMService:</b> Handles Excel import via EPPlus — parses and validates BOM data (columns: Item, Quantity, Reference, Part/Value, Voltage, Technology, Tolerance, Package, Manufacturer, Order Code, Supplier), classifies components per 16 EEC categories, assigns designator types<br>
    • <b>DisassemblyService:</b> Manages step-by-step instructions, maps each step to A-L chest, tracks operator progress, calculates material value (€/t * mass)<br>
    • <b>MaterialValueService:</b> Calculates financial value per material based on current market prices (e.g., AISI430: 500€/t, AISI304L: 1,700€/t, AISI316L: 2,800€/t)<br>
    • <b>AuditService:</b> Records all operations with timestamp, user, device, action, chest used, material mass for regulatory compliance<br>
    • <b>EECClassifier:</b> Classifies components into the 16 EEC categories and their subcategories<br>
    • <b>DesignatorValidator:</b> Validates reference designators against the 55+ known types<br>
    • <b>DisassemblyStep:</b> Domain entity for each step (text instruction, image path, order number, target chest A-L)<br>
    • <b>AuditLog:</b> Domain entity for operation tracking with full traceability
    </p>
</details>

#### 5.2 Dynamic Models

<details> 
    <summary> Workflow for BOM import and disassembly guidance </summary>
    <p><b>BOM Import Flow:</b><br>
    (1) User uploads Excel file → (2) BOMService parses via EPPlus → (3) EECClassifier assigns EEC categories (1-16) to each component → (4) DesignatorValidator checks reference designators → (5) Device, BOMEntry, Component entities created/updated → (6) Material declarations linked to components via CASRN → (7) Validation report returned to user with any warnings (missing data, unknown designators)</p>
    <p><b>Disassembly Flow (Physical Line):</b><br>
    (1) Operator at workstation 3-4 selects identified device on monitor 6-7 → (2) DisassemblyService retrieves step list → (3) Frontend renders step with text instruction and visual highlight → (4) Color code displayed showing target chest (A-L) for current material → (5) Operator performs disassembly, places part in correct chest → (6) Operator marks step complete → (7) Material mass recorded in audit log → (8) Next step displayed until device fully disassembled → (9) Recovery summary shown (materials sorted, estimated value, chest utilization)</p>
    <p><b>Material Value Calculation:</b><br>
    (1) For each sorted component, MaterialValueService retrieves material type → (2) Looks up current market price (€/t) → (3) Calculates: value = (material_mass_mg / 1,000,000,000) * market_price_eur_per_ton → (4) Aggregates by material type for the device summary report</p>
</details>
