### User Requirements Specification Document

##### DIBRIS – Università di Genova. Scuola Politecnica, Software Engineering Course 80154

**VERSION : 1.0**

**Authors**
Tropeano Luca

**REVISION HISTORY**

| Version | Date | Authors | Notes |
| --- | --- | --- | --- |
| 1.0 | 27/06/2026 | Tropeano | First complete draft based on project files |

# Table of Contents

1. [Introduction](#p1)
  1. [Document Scope](#sp1.1)
  2. [Definitions and Acronyms](#sp1.2)
  3. [References](#sp1.3)
2. [System Description](#p2)
  1. [Context and Motivation](#sp2.1)
  2. [Project Objectives](#sp2.2)
  3. [EEC Component Classification](#sp2.3)
  4. [Designators Standard](#sp2.4)
3. [Requirements](#p3)
  1. [Stakeholders](#sp3.1)
  2. [Functional Requirements](#sp3.2)
  3. [Non-Functional Requirements](#sp3.3)
  4. [Data Requirements](#sp3.4)

## 1. Introduction

### 1.1 Document Scope

This document defines the user requirements for the **Ariadne Data-driven Materials Recovery System** (Italian Patent No. 102019000014451, European Patent No. EP4010822), a software platform for the recognition, classification, and material recovery optimization of Waste Electrical and Electronic Equipment (WEEE).

The core objective, as defined at **Punto C1** of the Ariadne data flow scheme, is to create a **structured database** containing the detailed list of materials present in electrical and electronic components. The DB — directly implemented in SQL (not Excel-based) — will be connected to the Ariadne platform to determine **quali, quanti e dove** (which, how many, where) the recoverable materials are located inside each device. Excel files are used solely as an **input format** for importing BOM and material declaration data into the database; the persistent storage is a properly implemented relational database.

The system supports recycling plant operators during the pre-treatment phase by identifying WEEE devices, retrieving Bill of Materials (BOM) and component material declarations from the DB, providing disassembly guidance with color-coded sorting, and tracking material recovery for audit and reporting.

### 1.2 Definitions and Acronyms

| Acronym | Definition |
| --- | --- |
| WEEE | Waste Electrical and Electronic Equipment |
| BOM | Bill of Materials |
| URS | User Requirements Specification |
| DRS | Design Requirement Specification |
| OCR | Optical Character Recognition |
| AI  | Artificial Intelligence |
| LLM | Large Language Model |
| CRM | Critical Raw Materials (EU Regulation 2024/1252) |
| EEC | Electronic Engineering Components (16-category classification) |
| PCB | Printed Circuit Board |
| AVI | Automatic Visual Inspection |
| SMD | Surface Mount Device |
| CASRN | Chemical Abstracts Service Registry Number |
| MD  | Material Declaration |
| MVP | Minimum Viable Product |
| API | Application Programming Interface |

### 1.3 References

- Document I – Problem Summary and General Requirements (doc1_tropeano.txt)
- Document II – Project Summary and Agreed Requirements (doc2.txt)
- Ariadne Project: System Requirements & Specifications (doc5.md)
- OpenCV Ariadne Pitch (1).pdf
- Ariadne Digital Path presentation (2026-6-19 Ariande Digital path Rev En 22 sl.pdf)
- Designators EEC -C1 index -X LUCA 2.xlsx (component classification and designators, with distributor list)
- Scheda STM-Steval Spin3204 BOM (reference BOM for testing)
- Email "Materiale visto insieme" (26/06/2026) — requirements for structured DB at C1 point, linked to Ariadne platform
- Email "Aggiornamento file Designators" (26/06/2026) — distributor catalog numbers for material declaration sourcing
- Roberto Mantello thesis — Excel template as trace for DB logical organization (the final DB will be more structured and capacious)
- EU Critical Raw Materials Act (Regulation EU 2024/1252)
- IEEE/ANSI Standard for Reference Designators

## 2. System Description

### 2.1 Context and Motivation

The electronics industry relies on more than 60 materials, at least 20 of which are critical and non-substitutable. Globally, industrialized countries generate up to **64 million tons of electronic waste** annually, making WEEE the fastest-growing waste stream (3–5% per year).

Current state-of-the-art recycling is based on mechanical shredding followed by coarse separation, recovering only **8–10 out of 50–60 elements** present in devices. Only high-volume materials (iron, aluminium, copper) or high-value materials (gold, silver, palladium) are economically recovered under current processes. Of the 34 Critical Raw Materials listed by the EU (CRMs), 14 exhibit **global end-of-life recycling rates of 0–5%**.

The **Ariadne system** bridges the gap between physical WEEE devices arriving at recycling facilities and the digital information describing their internal composition, enabling informed disassembly and targeted material recovery.

### 2.2 Project Objectives

The primary goal of the system is to cover the entire lifecycle of device processing:

- **Product Identification:** Recognizing the device model via images, serial numbers, or barcodes/QR codes
- **Structured Materials DB (C1):** Creazione di un database strutturato con l'elenco dettagliato dei materiali contenuti nei componenti elettrici ed elettronici (Punto C1 del flusso dati Ariadne), che definisca **quali, quanti e dove** si trovano i materiali recuperabili in un apparecchio
- **BOM & Material Declaration Retrieval:** Import di BOM da file Excel (formato di input) nel database SQL, linking each component to its Material Declaration
- **Component Recognition:** Identifying internal parts using computer vision (OpenCV) and AI (LLMs for document processing)
- **Disassembly Guidance:** Providing step-by-step instructions with color-coded material sorting (A-L container system)
- **Material Recovery Optimization:** Calculating recoverable materials, estimated weight, and financial value per material type
- **Audit & Traceability:** Logging all operations for regulatory compliance

### 2.3 EEC Component Classification

The system shall adopt the **16-category EEC (Electronic Engineering Components) index** for classifying electronic parts:

| #   | Category | Subcategories |
| --- | --- | --- |
| 1   | Cable Assemblies | Data Transmission, Fiber Optic, RF-Microwave Assemblies |
| 2   | Capacitors | Aluminum Solid, Ceramic, Film, Glass, Mica, Semiconductor, Tantalum |
| 3   | Connectors | Circular, D-Shaped, PCB, RF Coaxial, Terminal Blocks |
| 4   | Crystals and Oscillators | Atomic Clocks, Crystal Oscillator, Quartz Crystal Unit |
| 5   | Discretes | Diodes (rectifier, Schottky, Zener, TVS, LED), Transistors (BJT, MOSFET, JFET, RF) |
| 6   | Filters | Common Mode Chokes, EMI-RFI, Ferrite Beads, SAW |
| 7   | Fuses and Fuseholders |     |
| 8   | Heaters |     |
| 9   | Inductors | Custom, Power, RF |
| 10  | Microcircuits | Clock/Timing, Communication/Interface, Sensors, Memory, Logic, Processor, Programmable Logic, Power Management, Signal Acquisition, RF-Microwave |
| 11  | Relays | Hybrid, Latching, Non-Latching, Solid State |
| 12  | Resistors | Film, Metal Foil, Network/Arrays, Jumper, Wire Wound |
| 13  | Switches | Microswitches, RF-Microwave, Snap Action, Thermostatic, Toggle |
| 14  | Thermistors | NTC, PTC, RTD |
| 15  | Transformers | Current Sense, Custom, Data Bus, Gate Drive, Power, Pulse, RF |
| 16  | Wires and Cables | Low Frequency, Other, RF Coaxial |

### 2.4 Designators Standard

The system shall support standard reference designators per IEEE/ANSI conventions, including but not limited to:

| Designator | Component |
| --- | --- |
| R   | Resistor |
| C   | Capacitor |
| L   | Inductor |
| D   | Diode, LED, Zener |
| Q   | Transistor, MOSFET, JFET, IGBT |
| U / IC | Integrated Circuit |
| J / P / X / CN / CONN | Connector |
| Y / XTAL | Crystal / Resonator |
| SW / S | Switch |
| F   | Fuse |
| FB  | Ferrite Bead |
| T   | Transformer |
| K / RL | Relay / Contactor |
| M   | Motor |
| B / BT | Battery |
| BZ / LS / SPK / MIC | Buzzer / Speaker / Microphone |
| ANT | Antenna |
| TP  | Test Point |
| JP / LK | Jumper / Link |
| H / MH / HS | Hardware (mounting hole, heat sink) |
| RV / VR | Variable Resistor / Trimmer / Potentiometer |
| MOV | Metal Oxide Varistor |
| TH / RT / NTC / PTC | Thermistor |
| PS / PSU | Power Supply |
| REG | Voltage Regulator |
| OSC | Oscillator |
| TB  | Terminal Block |
| DS / DISP / LCD | Display |
| GDT | Gas Discharge Tube |
| TVS | TVS Diode |
| ESD | ESD Protection |
| Z   | Zener Diode |

## 3. Requirements

| Priority | Meaning |
| --- | --- |
| M   | **Mandatory:** Essential requirement that must be implemented |
| D   | **Desiderable:** Important but not strictly necessary |
| O   | **Optional:** Would be nice to have |
| E   | **Future Enhancement:** Planned for later releases |

### 3.1 Stakeholders

| Stakeholder | Role |
| --- | --- |
| Plant Operator | Uses the tool on the recycling line to identify devices and follow disassembly guidance |
| Technician | Handles edge cases, manual corrections, and system feedback |
| Supervisor | Monitors recovery metrics, reviews logs, and manages material tracking |
| Manufacturer | Provides BOM and material declaration data for devices |
| System Developer | Designs, develops, and maintains the system |
| Ariadne Platform Admin | Manages the central Ariadne data platform and data exchange |

### 3.2 Functional Requirements

| ID  | Description | Priority |
| --- | --- | --- |
| FR1 | The system shall identify and classify WEEE devices from images (via OpenCV), serial numbers, barcodes, or QR codes | M   |
| FR2 | The system shall recognize both the product family and the exact model, including legacy or damaged devices, using feature matching (SIFT/ORB) and AI inference | M   |
| FR3 | The system shall retrieve and display the Bill of Materials for the identified device from the SQL database (not from Excel files directly) | M   |
| FR4 | For each component, the system shall display: manufacturer, manufacturer ordering code, reference designator, material type (with CASRN), quantity, package, physical position on PCB, estimated weight (mg), and financial value (€/t) | M   |
| FR5 | The system shall use the EEC 16-category index to classify components in the BOM | M   |
| FR6 | The system shall support standard reference designators (IEEE/ANSI, 55+ types) for component identification | M   |
| FR7 | The system shall provide step-by-step disassembly instructions with visual aids (color-coded materials per A-L sorting chests) | M   |
| FR8 | The system shall guide operators on placing recovered materials into the correct color-coded sorting chests (A-L) | M   |
| FR9 | The system shall calculate and display material recovery value based on current market prices per material type | M   |
| FR10 | The system shall allow operators to manually correct misidentified devices or components | D   |
| FR11 | Operator corrections and feedback shall be stored for future AI model improvement | D   |
| FR12 | The system shall maintain a traceability log of all operations (timestamp, user, device, action, materials sorted) for auditing purposes | M   |
| FR13 | The system shall be a web-based application accessible via browser on tablets or workstations used on the recycling line | M   |
| FR14 | The system shall integrate with the Ariadne data platform for BOM exchange, material data, and digital product passports | M   |
| FR15 | The system shall import BOM files in Excel format (via EPPlus) as an input method, then store the parsed data in the SQL database — Excel is never used as persistent storage | M   |
| FR16 | The system shall support import of Material Declarations from manufacturers, linking each component to its chemical composition in the DB | M   |
| FR17 | The system shall store material data with CAS Registry Numbers (CASRN) for precise chemical identification in the DB | M   |
| FR18 | The system shall distinguish between element materials and compounds (organic/inorganic) in material declarations stored in the DB | M   |
| FR19 | The system shall present top-K recognition matches with confidence scores when exact identification is uncertain | D   |
| FR20 | The system shall allow technicians to manually enter device data for products without digital BOM | D   |
| FR21 | The system shall include in the DB the list of major electronic component distributors (Arrow, Avnet, Mouser, DigiKey, Farnell, RS, TME, etc.) with their catalog numbers for each component, to facilitate material declaration sourcing | O   |
| FR22 | The DB structure shall be organized following the logical trace from the thesis Excel template, but the final database shall be more structured, more capacious, and implemented directly in SQL (not Excel) | M   |

### 3.3 Non-Functional Requirements

| ID  | Description | Priority |
| --- | --- | --- |
| NFR1 | The system shall be easy to use by operators with limited technical expertise (intuitive UI with visual guidance) | M   |
| NFR2 | Device identification shall complete in < 5 seconds for real-time operation | M   |
| NFR3 | The system shall ensure reasonable accuracy in device recognition using OpenCV feature matching and AI fallback | M   |
| NFR4 | The system shall be robust and operate even with incomplete, damaged, or dirty devices | D   |
| NFR5 | The system shall be scalable to support 1000+ device models and all 16 EEC categories | D   |
| NFR6 | The system shall allow updates of device data, materials, and components via Excel import (EPPlus) | M   |
| NFR7 | The system shall ensure data consistency and correctness of material information (validation on import) | M   |
| NFR8 | The system shall support integration with external systems, including AI-based LLM modules and external databases | D   |
| NFR9 | The system shall maintain a complete audit log for traceability of disassembly and recovery processes | M   |
| NFR10 | The system shall store material masses in mg (milligrams) as the standard unit of measurement | M   |
| NFR11 | The system shall support list of  all major electronic component distributors (Arrow, Avnet, Mouser, DigiKey, Farnell, RS, TME, etc.) for catalog number cross-referencing | O   |

### 3.4 Data Requirements

| ID  | Description | Priority |
| --- | --- | --- |
| DR1 | All persistent data shall be stored in a **directly implemented SQL database**. Excel is used only as an import/input format and never as a storage layer. The thesis Excel template is a logical trace only — the final DB is more structured and capacious | M   |
| DR2 | The system shall store a complete device catalog with: model name, manufacturer, product family, EEC categories | M   |
| DR3 | The system shall store BOM data with: item number, quantity, reference designators, part value, voltage/wattage, technology type, tolerance, package, manufacturer, ordering code, supplier, supplier ordering code | M   |
| DR4 | The system shall store material declarations per component with: material type, CASRN, mass (mg), percentage composition, element/compound classification | M   |
| DR5 | The system shall store disassembly instructions with: step number, text instruction, image(s), target sorting chest (A-L), material type | M   |
| DR6 | The system shall store distributor/reseller information: name, catalog number for each component, notes — to track which distributors have the easiest path to obtain Material Declarations | O   |
| DR7 | The system shall link each BOM component to one or more reference designators | M   |
| DR8 | The DB shall enable querying by: **which** materials, **how many** (quantity/mass), and **where** (component/position) they are located in a device, as per the C1 data flow requirement | M   |
