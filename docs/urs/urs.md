### User Requirements Specification Document

##### DIBRIS – Università di Genova. Scuola Politecnica, Software Engineering Course 80154

**VERSION : 1.2**

**Authors**
Tropeano Luca

**REVISION HISTORY**

| Version | Date       | Authors  | Notes                                          |
| ------- | ---------- | -------- | ---------------------------------------------- |
| 1.0     | 27/06/2026 | Tropeano | First complete draft based on project files     |
| 1.1     | 28/06/2026 | Tropeano | Revision after Rosario feedback — scope focused on C1 components only |
| 1.2     | 02/07/2026 | Tropeano | Revision after Rosario feedback v2: C1 defined, SMT/THT, RoHS, predictive algorithms, URS/DRS alignment |

# Table of Contents

1. [Introduction](#p1)
   1. [Document Scope](#sp1.1)
   2. [Definitions and Acronyms](#sp1.2)
   3. [References](#sp1.3)
2. [System Description](#p2)
   1. [Context and Motivation](#sp2.1)
   2. [Project Scope and Objectives](#sp2.2)
   3. [C1-C2-C3 Framework](#sp2.3)
   4. [EEC Component Classification](#sp2.4)
   5. [Designators Standard](#sp2.5)
3. [Requirements](#p3)
   1. [Stakeholders](#sp3.1)
   2. [Functional Requirements](#sp3.2)
   3. [Non-Functional Requirements](#sp3.3)
   4. [Data Requirements](#sp3.4)

<a name="p1"></a>

## 1. Introduction

<a name="sp1.1"></a>

### 1.1 Document Scope

This document defines the user requirements for the **Ariadne Data-driven Materials Recovery System** (Italian Patent No. 102019000014451, European Patent No. EP4010822).

The primary objective, as defined at **Point C1** of the Ariadne data flow scheme, is to create a **structured SQL database** containing the detailed list of materials present in **C1 components** — electrical and electronic components in their minimal functional form that cannot be further simplified/disassembled without losing their characteristics (e.g. resistors, capacitors, transistors, ICs, diodes, connectors, crystals). The DB will be connected to the Ariadne platform to determine **quali, quanti e dove** (which, how many, where) the recoverable materials are located inside each device.

**Scope restriction — Phase 1: C1 components only.** This phase focuses exclusively on **primary electrical/electronic components** (C1) as found on PCBs. These are components in their minimal functional form that cannot be further simplified/disassembled without losing their characteristics. Large appliances, disassembly guidance, material sorting, and market value calculations are out of scope for this phase.

Excel files (.xlsx) are used solely as an **input format** for importing BOM data. The persistent storage is a directly implemented SQL Server database — not Excel.

<a name="sp1.2"></a>

### 1.2 Definitions and Acronyms

| Acronym | Definition |
| ------- | ---------- |
| AEE     | Apparecchiature Elettriche ed Elettroniche (Italian for EEE) |
| RAEE    | Rifiuti da AEE (WEEE) |
| BOM     | Bill of Materials / Distinta Base |
| MDF     | Materials Declaration Form / Materials Declaration Sheet |
| URS     | User Requirements Specification |
| DRS     | Design Requirement Specification |
| OCR     | Optical Character Recognition |
| AI      | Artificial Intelligence |
| LLM     | Large Language Model |
| CRM     | Critical Raw Materials (EU Regulation 2024/1252) |
| EEC     | Electronic Engineering Components (16-category classification) |
| PCB     | Printed Circuit Board |
| SMD     | Surface Mount Device |
| SMT     | Surface-Mount Technology |
| THT     | Through-Hole Technology |
| RoHS    | Restriction of Hazardous Substances (Dir. 2011/65/EU) |
| CASRN   | Chemical Abstracts Service Registry Number |
| MD      | Material Declaration (also MDF) |
| C1      | Primary electrical/electronic components |
| C2      | Semi-finished products / subassemblies |
| C3      | Finished products ready for market |

<a name="sp1.3"></a>

### 1.3 References

- Document I – Problem Summary and General Requirements (doc1_tropeano.txt)
- Document II – Project Summary and Agreed Requirements (doc2.txt)
- Ariadne Project: System Requirements & Specifications (doc5.md)
- Ariadne Digital Path presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)
- Designators EEC -C1 index -X LUCA 2.xlsx
- Scheda STM-Steval Spin3204 BOM (reference BOM for C1 component testing)
- Email "Materiale visto insieme" (26/06/2026)
- Email "Aggiornamento file Designators" (26/06/2026)
- Revision notes from Rosario Capponi (0 REV 1 R - Sistema Ariadne data driven Materials recovery.docx)
- EU Critical Raw Materials Act (Regulation EU 2024/1252)
- IEEE/ANSI Standard for Reference Designators

<a name="p2"></a>

## 2. System Description

<a name="sp2.1"></a>

### 2.1 Context and Motivation

The electronics industry relies on more than 60 materials, at least 20 of which are critical and non-substitutable. Globally, industrialized countries generate up to **64 million tons of electronic waste** annually, making WEEE the fastest-growing waste stream (3–5% per year).

Current state-of-the-art recycling is based on mechanical shredding followed by coarse separation, recovering only **8–10 out of 50–60 elements** present in devices. Of the 34 Critical Raw Materials listed by the EU (CRMs), 14 exhibit **global end-of-life recycling rates of 0–5%**.

The **Ariadne system** bridges the gap between physical WEEE devices arriving at recycling facilities and the digital information describing their internal composition. The first step — and the focus of this project — is building a structured database of materials present in C1 components, starting from real BOMs and their corresponding Material Declaration Forms.

<a name="sp2.2"></a>

### 2.2 Project Scope and Objectives

**Phase 1 scope** (this document):
- Import BOMs from manufacturers (Excel format) to obtain a list of C1 components
- For each component, retrieve the corresponding **Material Declaration Form (MDF)** from the manufacturer or distributor
- Extract material composition data from MDFs (typically PDF) and store it in a structured SQL database
- Define the most efficient and reliable pipeline: **MDF (PDF) → [optional Excel intermediate for validation] → SQL DB**
- Enable queries to determine **which** materials, **how many** (mass), and **where** (which component) they are located

**Future phases** (not covered by this document):
- C2 components (semi-finished products / subassemblies)
- C3 components (finished products with Digital Product Passport)
- Computer vision recognition (OpenCV) for device identification
- AI/LLM for automated MDF parsing
- Disassembly guidance for large appliances
- Material sorting (A-L chests)
- Market value calculation

<a name="sp2.3"></a>

### 2.3 C1-C2-C3 Framework

The Ariadne platform classifies components into three levels:

| Level | Definition | Examples |
|-------|-----------|----------|
| **C1** | Primary electrical/electronic components — minimal functional form, cannot be further simplified/disassembled without losing their characteristics | Resistors, capacitors, transistors, ICs, diodes, connectors, crystals |
| **C2** | Semi-finished products / subassemblies | PCB assemblies, power supply modules, display assemblies |
| **C3** | Finished products ready for market | Mobile phones, laptops, washing machines |

**Phase 1 of this project covers only C1 components**, using real PCB BOMs as the source for component lists.

<a name="sp2.4"></a>

### 2.4 EEC Component Classification

The system shall adopt the **16-category EEC (Electronic Engineering Components) index** for classifying electronic parts:

| # | Category | Subcategories |
|---|----------|---------------|
| 1 | Cable Assemblies | Data Transmission, Fiber Optic, RF-Microwave Assemblies |
| 2 | Capacitors | Aluminum Solid, Ceramic, Film, Glass, Mica, Semiconductor, Tantalum |
| 3 | Connectors | Circular, D-Shaped, PCB, RF Coaxial, Terminal Blocks |
| 4 | Crystals and Oscillators | Atomic Clocks, Crystal Oscillator, Quartz Crystal Unit |
| 5 | Discretes | Diodes (rectifier, Schottky, Zener, TVS, LED), Transistors (BJT, MOSFET, JFET, RF) |
| 6 | Filters | Common Mode Chokes, EMI-RFI, Ferrite Beads, SAW |
| 7 | Fuses and Fuseholders | |
| 8 | Heaters | |
| 9 | Inductors | Custom, Power, RF |
| 10 | Microcircuits | Clock/Timing, Communication/Interface, Sensors, Memory, Logic, Processor, Programmable Logic, Power Management, Signal Acquisition, RF-Microwave |
| 11 | Relays | Hybrid, Latching, Non-Latching, Solid State |
| 12 | Resistors | Film, Metal Foil, Network/Arrays, Jumper, Wire Wound |
| 13 | Switches | Microswitches, RF-Microwave, Snap Action, Thermostatic, Toggle |
| 14 | Thermistors | NTC, PTC, RTD |
| 15 | Transformers | Current Sense, Custom, Data Bus, Gate Drive, Power, Pulse, RF |
| 16 | Wires and Cables | Low Frequency, Other, RF Coaxial |

Note: The EEC category is distinct from the reference designator (e.g., a "R" designator always maps to category 12 "Resistors", a "C" to category 2 "Capacitors").

<a name="sp2.5"></a>

### 2.5 Designators Standard

The system shall support standard reference designators per IEEE/ANSI conventions:

| Designator | Component |
|------------|-----------|
| R | Resistor |
| C | Capacitor |
| L | Inductor |
| D | Diode, LED, Zener |
| Q | Transistor, MOSFET, JFET, IGBT |
| U / IC | Integrated Circuit |
| J / P / X / CN / CONN | Connector |
| Y / XTAL | Crystal / Resonator |
| SW / S | Switch |
| F | Fuse |
| FB | Ferrite Bead |
| T | Transformer |
| K / RL | Relay / Contactor |
| M | Motor |
| B / BT | Battery |
| BZ / LS / SPK / MIC | Buzzer / Speaker / Microphone |
| ANT | Antenna |
| TP | Test Point |
| JP / LK | Jumper / Link |
| H / MH / HS | Hardware (mounting hole, heat sink) |
| RV / VR | Variable Resistor / Trimmer / Potentiometer |
| MOV | Metal Oxide Varistor |
| TH / RT / NTC / PTC | Thermistor |
| PS / PSU | Power Supply |
| REG | Voltage Regulator |
| OSC | Oscillator |
| TB | Terminal Block |
| DS / DISP / LCD | Display |
| GDT | Gas Discharge Tube |
| TVS | TVS Diode |
| ESD | ESD Protection |
| Z | Zener Diode |

<a name="p3"></a>

## 3. Requirements

| Priority | Meaning |
| -------- | ------- |
| M | **Mandatory:** Essential requirement that must be implemented |
| D | **Desiderable:** Important but not strictly necessary |
| O | **Optional:** Would be nice to have |
| E | **Future Enhancement:** Planned for later releases |

<a name="sp3.1"></a>

### 3.1 Stakeholders

| Stakeholder | Role |
| ----------- | ---- |
| System Developer | Designs, develops, and maintains the system |
| Ariadne Platform Admin | Manages the central Ariadne data platform and data exchange |
| Manufacturer | Provides BOM and Material Declaration Forms for C1 components |
| Researcher / Data Analyst | Analyzes material composition data from the database |

<a name="sp3.2"></a>

### 3.2 Functional Requirements

| ID | Description | Priority |
| -- | ----------- | -------- |
| FR1 | The system shall import BOM files, initially in Excel format (via EPPlus) for the testing/verification phase, to obtain a list of C1 components. After the initial phase, direct import from other sources may replace the Excel step — Excel is never used as persistent storage | M |
| FR2 | The system shall support BOM columns: Item, Quantity, Reference Designator, Part/Value, Manufacturer, Manufacturer Order Code, Supplier 1/2/3, Supplier 1/2/3 Order Code | M |
| FR3 | The system shall use the EEC 16-category index to classify each component in the BOM. The EEC category must be compared with the designator column in the BOM (if present); otherwise it must be assigned automatically — it must always be present | M |
| FR4 | The system shall support standard reference designators (IEEE/ANSI, 55+ types) for component identification | M |
| FR5 | For each BOM component, the system shall store the corresponding Material Declaration Form (MDF) data: material name (English), CASRN, mass (mg), and any materials used under RoHS exemption | M |
| FR6 | The system shall distinguish between element materials and compounds (organic/inorganic) in material declarations | M |
| FR7 | The system shall support recording up to 3 suppliers per component with their respective catalog numbers, to facilitate MDF sourcing | O |
| FR8 | The system shall store device/PCB metadata: brand, model name, manufacturer, year of production | M |
| FR9 | The system shall enable querying by: **which** materials, **how many** (mass), and **where** (component/designator) they are located in a device | M |
| FR10 | The system shall support an **optional intermediate Excel export** for manual verification of AI-extracted MDF data before committing to the SQL DB (Note: AI/LLM for MDF parsing is planned for future phases; the intermediate Excel step provides a manual verification safety check during transition) | D |
| FR11 | The system shall be a web-based application accessible via browser | M |
| FR12 | The system shall integrate with the Ariadne data platform for data exchange and future expansion to C2/C3 | M |
| FR13 | The system shall allow manual entry of component data for products without digital BOM | D |
| FR14 | The system shall support the use of average/estimated material composition data for components where the original MDF is not available, based on data from similar known components. This will enable predictive algorithms (future development) for estimating composition of components without direct MDF sourcing | D |

**Note regarding AI/LLM, OpenCV, disassembly guidance, sorting chests, and market values:** These features are intentionally excluded from Phase 1. They will be developed in subsequent phases of the Ariadne platform roadmap.

<a name="sp3.3"></a>

### 3.3 Non-Functional Requirements

| ID | Description | Priority |
| -- | ----------- | -------- |
| NFR1 | The system shall be easy to use for data entry and querying | M |
| NFR2 | The system shall allow updates of device data, BOMs, and materials via Excel import (EPPlus) | M |
| NFR3 | The system shall ensure data consistency and correctness of material information (validation on import) | M |
| NFR4 | The system shall store material masses in mg (milligrams) as the standard unit of measurement | M |
| NFR5 | The system shall be scalable to support 1000+ device models and all 16 EEC categories | D |
| NFR6 | The system shall support integration with external systems, including AI-based modules for MDF parsing (future phase) | D |
| NFR7 | Material names in the DB shall be stored in English | M |

<a name="sp3.4"></a>

### 3.4 Data Requirements

| ID | Description | Priority |
| -- | ----------- | -------- |
| DR1 | All persistent data shall be stored in a directly implemented SQL Server database. Excel is used only as an import/input format and never as a storage layer | M |
| DR2 | The system shall store device/PCB data with: brand, model name, manufacturer, year of production | M |
| DR3 | The system shall store BOM data with: item number, quantity, reference designators, mounting type (SMT/THT), part value, manufacturer, manufacturer order code, supplier 1/2/3, supplier 1/2/3 order codes | M |
| DR4 | The system shall store material declarations per component with: material name (English), CASRN, mass (mg), element/compound classification | M |
| DR5 | The system shall store the 16 EEC categories with subcategories for component classification | M |
| DR6 | The system shall store reference designators (55+ types, IEEE/ANSI) linked to EEC categories | M |
| DR7 | The DB shall enable querying by: **which** materials, **how many** (quantity/mass), and **where** (component/position) they are located in a device | M |
