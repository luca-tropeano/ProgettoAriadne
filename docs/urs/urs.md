### User Requirements Specification

##### DIBRIS – University of Genoa. Polytechnic School, Software Engineering Course 80154

**VERSION : 1.7**

**Authors**
Tropeano Luca

**REVISION HISTORY**

| Version | Date       | Authors | Notes                                                                              |
| ------- | ---------- | ------- | ---------------------------------------------------------------------------------- |
| 1.0     | 27/06/2026 | Tropeano | First complete draft based on project files                                        |
| 1.1     | 28/06/2026 | Tropeano | Revision after Rosario's feedback — scope focused on C1 components only            |
| 1.2     | 02/07/2026 | Tropeano | Rosario feedback revision v2: C1 defined, SMT/THT, RoHS, predictive algorithms, URS/DRS alignment |
| 1.3     | 02/07/2026 | Tropeano | Strapi integration: switched from direct SQL Server to Strapi headless CMS + PostgreSQL, all DB access via REST API |
| 1.4     | 22/07/2026 | Tropeano | PDF AI extraction implemented (FR10, NFR6 updated), device linking/auto-creation (FR8), Excel column mapping corrected, API token optional, export tool added, CLI flags --brand/--model/--manufacturer/--year |
| 1.5     | 12/08/2026 | Tropeano | CSV import support (FR9), EEC auto-classification (FR7), duplicate BOM check, DB→Excel export (FR14), DeepSeek AI as paid fallback. 47 tests, 350/350 components from 5 real BOMs. |
| 1.6     | 12/08/2026 | Tropeano | MongoDB raw-data storage (NFR8 data retention): raw documents archived before processing. Optional, offline degradation. 54 tests. |
| 1.7     | 12/08/2026 | Tropeano | OpenDocument (.ods) import support (FR9): dynamic schema, real HILTOP Motherboard BOM (160/160). 115 tests, 93% coverage. |

# Index

- [Index](#index)
  - [1. Introduction](#1-introduction)
    - [1.1 Document Scope](#11-document-scope)
    - [1.2 Definitions and Acronyms](#12-definitions-and-acronyms)
    - [1.3 References](#13-references)
  - [2. System Description](#2-system-description)
    - - [2.1 Context and Motivation](#21-context-and-motivation)
    - [2.2 Project Scope and Objectives](#22-project-scope-and-objectives)
    - [2.3 C1-C2-C3 Framework](#23-c1-c2-c3-framework)
    - [2.4 EEC Component Classification](#24-eec-component-classification)
    - [2.5 Designators Standard](#25-designators-standard)
  - [3. Requirements](#3-requirements)
    - [3.1 Stakeholders](#31-stakeholders)
    - [3.2 Functional Requirements](#32-functional-requirements)
    - [3.3 Non-Functional Requirements](#33-non-functional-requirements)
    - [3.4 Data Requirements](#34-data-requirements)

<a id="p1"></a>

## 1. Introduction

<a id="sp1.1"></a>

### 1.1 Document Scope

This document defines the user requirements for the **Ariadne Data-Driven Materials Recovery System** (Italian Patent No. 102019000014451, European Patent No. EP4010822).

The primary objective, defined at **Point C1** of the Ariadne data flow scheme, is the creation of a **structured SQL database** containing the detailed list of materials present in **C1 components** — electrical and electronic components in their minimum functional form, not further simplifiable/disassemblable without losing their characteristics (e.g., resistors, capacitors, transistors, ICs, diodes, connectors, crystals). The DB will be linked to the Ariadne platform to determine **which, how many, and where** recoverable materials are located within each device.

**Note on "WHERE":** At the C1 component level, "where" indicates **in which component** (which BOM entry, identified by reference designator) a material is found, not the internal position within the component itself. Although some MDFs report material distribution inside a single component (e.g., encapsulation, terminals, die), this distinction is not technically relevant for recovery purposes — it is not possible to separate elements so intimately connected within a single component (e.g., a resistor or microprocessor). For each element/material, the system stores its total mass per individual component.

**Scope restriction — Phase 1: C1 components only.** This phase focuses exclusively on **primary electrical/electronic components (C1)** as those found on PCBs. These are components in their minimum functional form, not further simplifiable/disassemblable without losing their characteristics. Large appliances, disassembly assistance, material sorting, and market value calculation are out of scope for this phase.

Excel files (.xlsx) are used exclusively as an **input format** for importing BOM data. All persistent data is stored in a database managed via **Strapi** (headless CMS, https://strapi.io/), accessible exclusively through its REST API. The underlying database is PostgreSQL. A CLI-based **database export tool** is available for generating Excel reports from Strapi data (6 sheets: Summary, EEC Categories, Reference Designators, BOM Entries, Devices, Audit Logs).

<a id="sp1.2"></a>

### 1.2 Definitions and Acronyms

| Acronym | Definition                                                              |
| ------- | ----------------------------------------------------------------------- |
| WEEE    | Waste Electrical and Electronic Equipment                               |
| RoHS    | Restriction of Hazardous Substances (Dir. 2011/65/EU)                  |
| BOM     | Bill of Materials                                                        |
| MDF     | Materials Declaration Form / Materials Declaration Sheet                 |
| URS     | User Requirements Specification                                         |
| DRS     | Design Requirement Specification                                        |
| OCR     | Optical Character Recognition                                           |
| AI      | Artificial Intelligence                                                 |
| LLM     | Large Language Model                                                     |
| CRM     | Critical Raw Materials (Regulation EU 2024/1252)                        |
| EEC     | Electronic Engineering Components (16-category classification)          |
| PCB     | Printed Circuit Board                                                    |
| SMD     | Surface Mount Device                                                     |
| SMT     | Surface-Mount Technology                                                |
| THT     | Through-Hole Technology                                                 |
| CASRN   | Chemical Abstracts Service Registry Number                               |
| MD      | Material Declaration (also MDF)                                         |
| C1      | Primary electrical/electronic components                                 |
| C2      | Semi-finished products / sub-assemblies                                  |
| C3      | Finished products ready for the market                                   |

<a id="sp1.3"></a>

### 1.3 References

- Document I – Problem Summary and General Requirements (doc1_tropeano.txt)
- Document II – Project Summary and Agreed Requirements (doc2.txt)
- Ariadne Project: System Requirements and Specifications (doc5.md)
- Ariadne Digital Path Presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)
- EEC Designators -C1 index -X LUCA 2.xlsx
- STM-Steval Spin3204 BOM Card (reference BOM for C1 component testing)
- Email "Materials discussed together" (26/06/2026)
- Email "Updated Designators file" (26/06/2026)
- Revision notes from Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)
- EU Critical Raw Materials Regulation (Regulation EU 2024/1252)
- IEEE/ANSI Reference Designators Standard
- Scheda STM-Steval Spin3204 - Copia x Luca.xlsx (real BOM Excel, 17 columns, header row 6)

<a id="p2"></a>

## 2. System Description

<a id="sp2.1"></a>

### 2.1 Context and Motivation

The electronics industry uses over 60 materials, at least 20 of which are critical and non-substitutable. Globally, industrialized countries generate up to **64 million tonnes of electronic waste** per year.

Traditional recycling relies on mechanical shredding which recovers only **8–10 elements out of 50–60** present in devices. Of the 34 Critical Raw Materials listed by the EU (CRM), 14 have **end-of-life global recycling rates of 0–5%**.

The **Ariadne system** bridges the gap between physical WEEE devices and digital information about their internal composition. The first step — and the focus of this project — is building a structured database of materials present in C1 components, starting from real BOMs and their corresponding Material Declaration Forms.

<a id="sp2.2"></a>

### 2.2 Project Scope and Objectives

**Phase 1 Scope** (this document):

- Import BOMs from manufacturers (Excel format) to obtain a list of C1 components
- For each component, retrieve the corresponding **Material Declaration Form (MDF)** from the manufacturer or distributor
- Extract material composition data from MDFs (typically PDF) and store them in a structured SQL database
- Define the most efficient and secure path: **MDF (PDF) → [optional intermediate Excel for validation] → Strapi API → PostgreSQL**
- Enable queries to determine **which** materials, **how many** (mass), and **where** (which component) they are located

**Future phases** (not covered by this document):

- C2 components (semi-finished products / sub-assemblies)
- C3 components (finished products with Digital Product Passport)
- Computer vision recognition (OpenCV) for device identification
- OCR for scanned/image PDFs (current PDF extraction requires text-based PDFs)
- Advanced MDF parsing with structured material breakdown
- Disassembly assistance for large WEEE
- Material sorting (containers A-L)
- Market value calculation

<a id="sp2.3"></a>

### 2.3 C1-C2-C3 Framework

The Ariadne platform classifies components into three levels:

| Level | Definition                                                                                                                                                        | Examples                                                          |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **C1** | Primary electrical/electronic components — minimum functional form, not further simplifiable/disassemblable without losing their characteristics               | Resistors, capacitors, transistors, ICs, diodes, connectors, crystals |
| **C2** | Semi-finished products / sub-assemblies                                                                                                                           | PCB assemblies, power supply modules, display assemblies          |
| **C3** | Finished products ready for the market                                                                                                                            | Mobile phones, computers, washing machines                       |

**Phase 1 of this project covers only C1 components**, using real PCB BOMs as the source for component lists.

<a id="sp2.4"></a>

### 2.4 EEC Component Classification

The system adopts the **EEC (Electronic Engineering Components) 16-category index** for classifying electronic parts:

| #   | Category                  | Subcategories                                                                            |
| --- | ------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | Cable Assemblies          | Data Transmission, Fiber Optic, RF-Microwave Assemblies                                  |
| 2   | Capacitors                | Aluminum Solid, Ceramic, Film, Glass, Mica, Semiconductor, Tantalum                     |
| 3   | Connectors                | Circular, D-Shaped, PCB, RF Coaxial, Terminal Blocks                                    |
| 4   | Crystals and Oscillators  | Atomic Clocks, Crystal Oscillator, Quartz                                               |
| 5   | Discretes                 | Diodes, Transistors (BJT, MOSFET, JFET, RF)                                             |
| 6   | Filters                   | Common Mode Suppressors, EMI-RFI, Ferrite Beads, SAW                                    |
| 7   | Fuses and Fuse Holders    |                                                                                         |
| 8   | Heaters                   |                                                                                         |
| 9   | Inductors                 | Custom, Power, RF                                                                        |
| 10  | Microcircuits             | Clock/Timing, Communication, Sensors, Memory, Logic, Processor, Power Management, RF    |
| 11  | Relays                    | Hybrid, Latching, Non-Latching, Solid State                                              |
| 12  | Resistors                 | Film, Metal, Networks/Arrays, Jumper, Wound                                              |
| 13  | Switches                  | Microswitches, RF, Snap-action, Thermostatic, Toggle                                     |
| 14  | Thermistors               | NTC, PTC, RTD                                                                            |
| 15  | Transformers              | Current Sensing, Custom, Data Bus, Power, Pulse, RF                                      |
| 16  | Wires and Cables          | Low Frequency, Other, RF Coaxial                                                         |

Note: The EEC category is distinct from the reference designator (e.g., a designator "R" always corresponds to category 12 "Resistors", a "C" to category 2 "Capacitors").

<a id="sp2.5"></a>

### 2.5 Designators Standard

The system supports standard reference designators according to IEEE/ANSI conventions:

| Designator            | Component                                       |
| --------------------- | ----------------------------------------------- |
| R                     | Resistor                                        |
| C                     | Capacitor                                       |
| L                     | Inductor                                        |
| D                     | Diode, LED, Zener                               |
| Q                     | Transistor, MOSFET, JFET, IGBT                  |
| U / IC                | Integrated Circuit                              |
| J / P / X / CN / CONN | Connector                                       |
| Y / XTAL              | Crystal / Resonator                             |
| SW / S                | Switch                                          |
| F                     | Fuse                                            |
| FB                    | Ferrite Bead                                    |
| T                     | Transformer                                     |
| K / RL                | Relay / Contactor                               |
| M                     | Motor                                           |
| B / BT                | Battery                                         |
| BZ / LS / SPK / MIC   | Buzzer / Speaker / Microphone                   |
| ANT                   | Antenna                                         |
| TP                    | Test Point                                      |
| JP / LK               | Jumper / Link                                   |
| H / MH / HS           | Hardware (mounting hole, heatsink)              |
| RV / VR               | Variable Resistor / Trimmer / Potentiometer     |
| MOV                   | Metal Oxide Varistor                            |
| TH / RT / NTC / PTC   | Thermistor                                      |
| PS / PSU              | Power Supply                                    |
| REG                   | Voltage Regulator                               |
| OSC                   | Oscillator                                      |
| TB                    | Terminal Block                                  |
| DS / DISP / LCD       | Display                                         |
| GDT                   | Gas Discharge Tube                              |
| TVS                   | TVS Diode                                       |
| ESD                   | ESD Protection                                  |
| Z                     | Zener Diode                                     |

<a id="p3"></a>

## 3. Requirements

| Priority | Meaning                                                                   |
| -------- | ------------------------------------------------------------------------- |
| M        | **Mandatory:** Essential requirement that must be implemented            |
| D        | **Desirable:** Important but not strictly necessary                      |
| O        | **Optional:** Nice to have                                               |
| E        | **Future Enhancement:** Planned for subsequent versions                  |

<a id="sp3.1"></a>

### 3.1 Stakeholders

| Stakeholder                        | Role                                                             |
| ---------------------------------- | ---------------------------------------------------------------- |
| System Developer                   | Designs, develops, and maintains the system                      |
| Ariadne Platform Admin             | Manages the central Ariadne platform and data exchange            |
| Manufacturer                       | Provides BOMs and Material Declaration Forms for C1 components    |
| Researcher / Data Analyst          | Analyzes material composition data from the database              |

<a id="sp3.2"></a>

### 3.2 Functional Requirements

| ID   | Description                                                                                                                                                                                           | Priority |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| FR1  | The system shall import BOM files, initially in Excel format (via openpyxl) for the testing/verification phase, to obtain a list of C1 components. After the initial phase, direct import from other sources may replace the Excel step — Excel is never used as persistent storage | M        |
| FR2  | The system shall support BOM columns: Item, Quantity, Reference Designator, Part Value, Manufacturer, Manufacturer Order Code, Supplier 1/2/3, Supplier 1/2/3 Order Codes                             | M        |
| FR3  | The system shall use the EEC 16-category index to classify each component in the BOM. The EEC category must be compared with the designator column in the BOM (if present); otherwise it must be assigned automatically — it must always be present                       | M        |
| FR4  | The system shall support standard reference designators (IEEE/ANSI, 55+ types) for component identification                                                                                                                                                           | M        |
| FR5  | For each BOM component, the system shall store the corresponding Material Declaration Form (MDF) data: material name (English), CASRN, mass (mg), and any materials used under RoHS exemption         | M        |
| FR6  | The system shall distinguish between elemental materials and compounds (organic/inorganic) in material declarations                                                                                   | M        |
| FR7  | The system shall support recording up to 3 suppliers per component with their respective catalog numbers, to facilitate MDF retrieval                                                                   | O        |
| FR8  | The system shall store device/PCB metadata: brand, model name, manufacturer, year of production. Devices are automatically created or retrieved during BOM import via CLI flags (--brand, --model, --manufacturer, --year), or linked to existing devices by model name | M        |
| FR9  | The system shall allow queries for: **which** materials, **how many** (mass), and **where** (component/designator) they are located in a device                                                         | M        |
| FR10 | The system shall support an **optional intermediate Excel export** for manual verification of AI-extracted MDF data before loading into the SQL DB. The current implementation parses BOM files from Excel (openpyxl) and from text-based PDFs via a direct regex parser (pdf_parser), with DeepSeek AI as a paid fallback only when the direct parser finds nothing (disabled by default via DEEPSEEK_ENABLED). Results are written to SQLite (local) and optionally synced to Strapi API (Note: OCR for scanned PDFs and advanced MDF parsing are planned for future phases) | D        |
| FR11 | The system shall be a web application accessible via browser                                                                                                                                           | M        |
| FR12 | The system shall integrate with the Ariadne data platform for data exchange and future expansion to C2/C3                                                                                             | M        |
| FR13 | The system shall allow manual entry of component data for products without a digital BOM                                                                                                               | D        |
| FR14 | The system shall support the use of average/estimated material composition data for components where the original MDF is not available, based on data from similar known components. This will enable predictive algorithms (future development) for estimating composition of components without direct MDF sourcing | D |

**Note on AI/LLM, OpenCV, disassembly assistance, sorting containers, and market values:** Text-based PDF BOMs are parsed by a direct regex parser (free). DeepSeek AI is integrated only as a paid fallback, disabled by default (`DEEPSEEK_ENABLED=false`) and used solely when the direct parser finds nothing. OCR for scanned PDFs, OpenCV computer vision, disassembly assistance, sorting containers, and market values are intentionally excluded from Phase 1 and will be developed in subsequent phases of the Ariadne platform roadmap.

<a id="sp3.3"></a>

### 3.3 Non-Functional Requirements

| ID   | Description                                                                                                              | Priority |
| ---- | ------------------------------------------------------------------------------------------------------------------------ | -------- |
| NFR1 | The system shall be easy to use for data entry and queries                                                              | M        |
| NFR2 | The system shall allow updates to devices, BOMs, and materials via Excel import (openpyxl)                                | M        |
| NFR3 | The system shall ensure consistency and correctness of material information (validation upon import)                     | M        |
| NFR4 | The system shall store material masses in mg (milligrams) as the standard unit of measure                                | M        |
| NFR5 | The system shall be scalable to support 1000+ device models and all 16 EEC categories                                   | D        |
| NFR6 | The system shall support integration with external systems, including AI modules for MDF parsing (DeepSeek API implemented as paid fallback for BOM extraction, disabled by default; advanced MDF parsing for subsequent phases) | D        |
| NFR7 | Material names in the DB shall be in English                                                                             | M        |

<a id="sp3.4"></a>

### 3.4 Data Requirements

| ID  | Description                                                                                                                                                                                               | Priority |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| DR1 | All persistent data shall be stored in a database managed via Strapi (headless CMS), accessed exclusively through its REST API. The underlying database is PostgreSQL. Excel is used only as an import/input format and never as a storage layer | M        |
| DR2 | The system shall store device/PCB data with: brand, model name, manufacturer, year of production                                                                                                          | M        |
| DR3 | The system shall store BOM data with: item number, quantity, reference designators, mounting type (SMT/THT), part value, manufacturer, manufacturer order code, supplier 1/2/3, supplier 1/2/3 order codes | M        |
| DR4 | The system shall store material declarations per component with: material name (English), CASRN, mass (mg), element/compound classification                                                               | M        |
| DR5 | The system shall store the 16 EEC categories with subcategories for component classification                                                                                                               | M        |
| DR6 | The system shall store reference designators (55+ types, IEEE/ANSI) linked to EEC categories                                                                                                               | M        |
| DR7 | The DB shall allow queries for: **which** materials, **how many** (quantity/mass), and **where** (component/position) they are located in a device                                                          | M        |
