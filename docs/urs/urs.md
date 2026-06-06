### User Requirements Specification Document
##### DIBRIS – Università di Genova. Scuola Politecnica, Software Engineering Course 80154

**VERSION : 1.0**

**Authors**
Tropeano Luca

**REVISION HISTORY**

| Version    | Date        | Authors      | Notes        |
| ----------- | ----------- | ----------- | ----------- |
| 1.0 | 06/06/2026 | Tropeano | First draft |

# Table of Contents

1. [Introduction](#p1)
	1. [Document Scope](#sp1.1)
	2. [Definitions and Acronyms](#sp1.2) 
	3. [References](#sp1.3)
2. [System Description](#p2)
	1. [Context and Motivation](#sp2.1)
	2. [Project Objectives](#sp2.2)
3. [Requirements](#p3)
	1. [Stakeholders](#sp3.1)
	2. [Functional Requirements](#sp3.2)
	3. [Non-Functional Requirements](#sp3.3)

<a name="p1"></a>

## 1. Introduction

<a name="sp1.1"></a>

### 1.1 Document Scope

This document defines the user requirements for the Ariadne Data-driven Materials Recovery System, a software tool for the recognition, classification, and material recovery optimization of Waste Electrical and Electronic Equipment (WEEE). The system supports recycling plant operators during the pre-treatment phase by identifying WEEE devices, retrieving Bill of Materials (BOM) and component data, providing disassembly guidance, and tracking material recovery for audit and reporting.

<a name="sp1.2"></a>

### 1.2 Definitions and Acronyms

| Acronym | Definition |
| ------- | ---------- |
| WEEE | Waste Electrical and Electronic Equipment |
| BOM | Bill of Materials |
| URS | User Requirements Specification |
| OCR | Optical Character Recognition |
| AI | Artificial Intelligence |
| MVP | Minimum Viable Product |

<a name="sp1.3"></a>

### 1.3 References

- Document I – Problem Summary and General Requirements (doc1_tropeano.txt)
- Document II – Project Summary and Agreed Requirements (doc2.txt)
- Ariadne Project: System Requirements & Specifications (doc5.md)
- OpenCV Ariadne Pitch (1).pdf

<a name="p2"></a>

## 2. System Description

<a name="sp2.1"></a>

### 2.1 Context and Motivation

The rapid growth of WEEE represents a major environmental and economic challenge. Modern electronic devices contain a large variety of valuable and critical raw materials, yet current recycling processes rely on mechanical shredding and coarse material separation, recovering only 8–10 out of more than 50–60 elements present in devices. This inefficiency is caused by the lack of connection between physical devices arriving at recycling facilities and the digital information describing their internal composition. The Ariadne system addresses this problem by creating a data-driven framework that connects manufacturers, data processing systems, and recycling facilities, leveraging digital product data, AI, and computer vision to enable optimized disassembly and material recovery.

<a name="sp2.2"></a>

### 2.2 Project Objectives

The primary goal of the system is to cover the entire lifecycle of device processing:

- **Product Identification:** Recognizing the device model via images, serial numbers, or barcodes
- **Component Recognition:** Identifying internal parts using computer vision (OpenCV)
- **Disassembly Guidance:** Providing step-by-step instructions for operators
- **Material Recovery Optimization:** Calculating recoverable materials based on BOM data

The expected final output includes model identification, a full list of components, material classification, disassembly instructions, and the estimated weight or value of recovered materials.

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
| Plant Operator | Uses the tool on the recycling line to identify devices and follow disassembly guidance |
| Technician | Handles edge cases, manual corrections, and system feedback |
| Supervisor | Monitors recovery metrics, reviews logs, and manages the system |
| Manufacturer | Provides BOM and material declaration data for devices |
| System Developer | Designs, develops and maintains the system |

<a name="sp3.2"></a>

### 3.2 Functional Requirements

| ID | Description | Priority |
| -- | ----------- | -------- |
| FR1 | The system shall identify and classify WEEE devices from images, serial numbers, barcodes, or QR codes | M |
| FR2 | The system shall recognize both the product family and the exact model when possible, including legacy or damaged devices | M |
| FR3 | The system shall retrieve and display the Bill of Materials for the identified device | M |
| FR4 | For each component, the system shall display material type, quantity, physical position, estimated weight and financial value | M |
| FR5 | The system shall provide step-by-step disassembly instructions with visual aids (highlights, color-coded materials) | M |
| FR6 | The system shall guide operators on placing recovered materials into the correct sorting chests | M |
| FR7 | The system shall allow operators to manually correct misidentified devices or components | D |
| FR8 | Operator corrections shall be stored for future AI training and system improvement | D |
| FR9 | The system shall maintain a traceability log of all operations for auditing purposes | M |
| FR10 | The system shall be a web-based application accessible on devices used on the recycling line | M |
| FR11 | The system shall integrate with the Ariadne data platform and related services | M |

<a name="sp3.3"></a>

### 3.3 Non-Functional Requirements

| ID | Description | Priority |
| -- | ----------- | -------- |
| NFR1 | The system should be easy to use by operators with limited technical expertise | M |
| NFR2 | The system should provide results in real time or near real time (device identification in < 5 seconds) | M |
| NFR3 | The system should ensure a reasonable level of accuracy in device recognition and classification | M |
| NFR4 | The system should be robust and able to operate even with incomplete or damaged devices | D |
| NFR5 | The system should be scalable to support 1000+ device models and additional WEEE categories | D |
| NFR6 | The system should allow updates of device data, materials, and components via Excel import | M |
| NFR7 | The system should ensure consistency and correctness of the provided information | M |
| NFR8 | The system should support integration with external systems, including AI-based modules and databases | D |
| NFR9 | The system should maintain a log for auditing purposes to track the disassembly and recovery process | M |
