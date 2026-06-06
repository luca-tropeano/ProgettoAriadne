# Ariadne Data-driven Materials Recovery System

## Design Requirement Specification Document

DIBRIS – Università di Genova. Scuola Politecnica, Corso di Ingegneria del Software 80154


<div align='right'> <b> Authors </b> <br> Tropeano </div>

### REVISION HISTORY

Version | Data | Author(s)| Notes
---------|------|--------|------
1 | 06/06/2026 | Tropeano | First Version of the document.

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

##  <a name="intro"></a>  1 Introduction
<details>
    <summary> The design specification document reflects the design and provides directions to the builders and coders of the product.</summary> 
    Through this document, designers communicate the design for the product to which the builders or coders must comply. The design specification should state how the design will meet the requirements.
</details>
    
### <a name="purpose"></a> 1.1 Purpose and Scope
<details> 
    <summary> The goal of this section is to describe the purpose of this document and intended audience </summary>
    <p>This document defines the design specifications for the Ariadne Data-driven Materials Recovery System. It translates the user requirements defined in the URS into a technical design that guides developers and builders. The intended audience includes software architects, developers, testers, and project stakeholders involved in the implementation phase.</p>
</details>

### <a name="def"></a> 1.2 Definitions
<details> 
    <summary> Key acronyms and terms used throughout the document </summary>
    <p>This subsection lists the acronyms and terms used in the design specification.</p>
    
| Term | Definition |
| ------------- | ------------- |
| WEEE | Waste Electrical and Electronic Equipment |
| BOM | Bill of Materials |
| DRS | Design Requirement Specification |
| OCR | Optical Character Recognition |
| API | Application Programming Interface |
| REST | Representational State Transfer |
| SIFT/ORB | Feature matching algorithms used in computer vision |
| EPPlus | .NET library for reading/writing Excel files |
    
</details>

### <a name="overview"></a> 1.3 Document Overview
<details> 
    <summary> Explain how is organized the document </summary>
    <p>Section 2 describes the project context, goals, technologies, and constraints. Section 3 provides the system overview including architecture, interfaces, and data flow. Sections 4 and 5 detail the two main system modules: the Recognition App and the Material Declaration App, including structural and dynamic models.</p>
</details>

### <a name="biblio"></a> 1.4 Bibliography
<details> 
    <summary> Reference documents </summary>
    <p>URS – User Requirements Specification (URS.md)<br>Document I – Problem Summary and General Requirements (doc1_tropeano.txt)<br>Document II – Project Summary and Agreed Requirements (doc2.txt)<br>Ariadne Project: System Requirements & Specifications (doc5.md)</p>
</details>

## <a name="description"></a> 2 Project Description

### <a name="project-intro"></a> 2.1 Project Introduction 
<details> 
    <summary> Describe at an high level what is the goal of the project and a possible solution </summary>
    <p>The Ariadne system addresses the inefficiency of current WEEE recycling processes. Most recycling plants rely on mechanical shredding recovering only 8–10 out of 50–60 elements. The proposed solution is a data-driven software tool that identifies WEEE devices via images or identifiers, retrieves BOM and material data, and provides disassembly guidance to operators. The system consists of two web applications: a Recognition App (computer vision-based device identification) and a Material Declaration App (BOM management, component mapping, and recovery tracking).</p>
</details>

### <a name="tech"></a> 2.2 Technologies used
<details> 
    <summary> Description of the overall architecture and technology stack </summary>
    <p>The system is built on the following technology stack:</p>

| Layer | Technology |
|-------|------------|
| Frontend | ASP.NET Core Blazor / Razor Pages |
| Backend | .NET / C# REST API |
| Database | SQL Server |
| Computer Vision | OpenCV (OpenCvSharp .NET wrapper) |
| BOM Import | EPPlus (Excel parsing) |
| OCR (optional) | Tesseract .NET |
| Hosting | IIS / Azure App Service |

</details>

### <a name="constraints"></a> 2.3 Assumptions and Constraints
<details> 
    <summary> Boundaries and assumptions that limit design choices </summary>
    <p>• BOM data is provided by manufacturers in Excel format<br>• Manuals may be scanned PDFs; OCR may be needed for text extraction<br>• Legacy devices without digital BOM require manual data entry<br>• The system operates in a plant environment with network connectivity<br>• Users have basic technical skills<br>• The system is a decision-support tool, not fully automated<br>• Development is in .NET and C# as per project requirements</p>
</details>

## <a name="system-overview"></a>  3 System Overview
<details> 
    <summary> High-level description of the system's structure and behavior </summary>
    <p>The Ariadne system is a web-based platform composed of two main applications that share a common backend and database. The Recognition App handles device identification via OpenCV and AI, while the Material Declaration App manages BOM data and material recovery tracking.</p>
</details>

### <a name="architecture"></a>  3.1 System Architecture
<details> 
    <summary> System architecture description and diagram </summary>
    <p>The system follows a three-tier architecture with a web client, an API gateway, and backend services. The main components are:</p>
    <pre>
[Web Client] ↔ [API Gateway] ↔ [Recognition Service]
                                 ├── [BOM Database (SQL Server)]
                                 ├── [Material Declaration Service]
                                 ├── [AI/OpenCV Module]
                                 └── [Audit Logger]
    </pre>
    <p>The backend services are stateless REST APIs, with the database handling all persistent state. OpenCV runs server-side for image preprocessing and feature matching.</p>
</details>

### <a name="interfaces"></a>  3.2 System Interfaces
<details> 
    <summary> External interfaces and interaction points </summary>
    <p>• <b>User Interface:</b> Web-based UI accessible via browser on tablets or workstations<br>• <b>Camera Interface:</b> Device camera capture for real-time image acquisition<br>• <b>File Import:</b> Excel BOM upload via EPPlus; PDF manual upload via file storage<br>• <b>API Interface:</b> RESTful endpoints for all system operations (device lookup, BOM retrieval, log access)<br>• <b>Database Interface:</b> SQL Server connection for persistent data storage</p>
</details>

### <a name="data"></a>  3.3 System Data
<details> 
    <summary> Data model overview and data flow </summary>
    <p>The system manages device data, BOM information, component materials, disassembly instructions, and audit logs. Data flows from input acquisition through recognition, enrichment, and presentation to the operator.</p>
</details>

#### <a name="inputs"></a>  3.3.1 System Inputs
<details> 
    <summary> Types of data the system receives </summary>
    <p>• Device images (internal/external view)<br>• Serial numbers (text input)<br>• Barcodes or QR codes (scanned)<br>• Excel BOM files from manufacturers<br>• PDF manuals (structured or scanned)<br>• Operator manual corrections and feedback</p>
</details>

#### <a name="outputs"></a>  3.3.2 System Outputs
<details> 
    <summary> Types of data the system produces </summary>
    <p>• Device identification result (model, family, confidence score)<br>• Bill of Materials with component list<br>• Material breakdown (type, quantity, weight, estimated value)<br>• Step-by-step disassembly instructions with visual aids<br>• Color-coded material sorting guidance<br>• Audit logs for traceability and reporting</p>
</details>

## <a name="sys-module-1"></a>  4 System Module 1 – Recognition App
<details> 
    <summary> The Recognition App handles device identification through computer vision and AI </summary>
    <p>This module accepts images or identifiers, processes them via OpenCV, matches against the device database, and returns the identified model with confidence. It also handles uncertainty by offering top-K matches and allowing manual override.</p>
</details>

### <a name="sd"></a>  4.1 Structural Diagrams
<details> 
    <summary> UML diagrams describing the static structure of the Recognition module </summary>
    <p>The module follows a Service-Repository pattern with clear separation between the API layer, recognition logic, and data access.</p>
</details>

#### <a name="cd"></a>  4.1.1 Class diagram
<details> 
    <summary> Main classes of the Recognition module </summary>
    <p>The core classes include RecognitionController (API endpoint), RecognitionService (business logic), DeviceRepository (data access), OpenCVService (image processing), and Device, Component, Material (domain models).</p>
</details>

##### <a name="cd-description"></a>  4.1.1.1 Class Description
<details> 
    <summary> Detailed description of each class in the Recognition module </summary>
    <p>• <b>RecognitionController:</b> REST API controller exposing endpoints for image upload, serial lookup, and manual correction<br>• <b>RecognitionService:</b> Orchestrates the recognition pipeline: image preprocessing, feature extraction, database matching, confidence scoring<br>• <b>DeviceRepository:</b> Data access layer for querying the device catalog, BOM data, and storing feedback<br>• <b>OpenCVService:</b> Wraps OpenCV operations (resize, denoise, SIFT/ORB feature matching)<br>• <b>Device:</b> Domain entity representing a WEEE device with model name, family, manufacturer<br>• <b>Component:</b> Domain entity for each part inside a device with type, position, material link<br>• <b>Material:</b> Domain entity with material type, quantity, weight, estimated value</p>
</details>

#### <a name="od"></a>  4.1.2 Object diagram
<details> 
    <summary> Example object instances at runtime </summary>
    <p>An example runtime configuration would include a Device instance "Smartphone Model X" linked to Component instances "Battery", "Display", "PCB", each associated with Material instances (Lithium, Glass, Gold, Copper) with respective quantities and estimated values.</p>
</details>

#### <a name="dm"></a>  4.2 Dynamic Models
<details> 
    <summary> Sequence and activity diagrams for key recognition workflows </summary>
    <p><b>Recognition Flow:</b> (1) User uploads image → (2) RecognitionController receives request → (3) RecognitionService calls OpenCVService for preprocessing → (4) Feature extraction performed → (5) DeviceRepository queried for matches → (6) Top-K results returned with confidence scores → (7) User confirms or corrects → (8) Feedback stored in database.</p>
</details>

## <a name="sys-module-2"></a>  5 System Module 2 – Material Declaration App
<details> 
    <summary> The Material Declaration App manages BOM data, component-material mapping, and recovery tracking </summary>
    <p>This module allows importing BOM Excel files, viewing device component trees with material breakdown, navigating disassembly steps, and tracking sorted materials against recovery targets.</p>
</details>

### <a name="sd2"></a>  5.1 Structural Diagrams
<details> 
    <summary> UML diagrams for the Material Declaration module </summary>
    <p>The module shares domain models with the Recognition module but adds services specific to BOM management, disassembly guidance, and audit logging.</p>
</details>

#### <a name="cd2"></a>  5.1.1 Class diagram
<details> 
    <summary> Main classes of the Material Declaration module </summary>
    <p>• <b>MaterialController:</b> REST API for BOM queries, disassembly steps, sorting instructions, and logs<br>• <b>BOMService:</b> Handles Excel import via EPPlus, parses and validates BOM data before persistence<br>• <b>DisassemblyService:</b> Manages step-by-step instructions, tracks operator progress<br>• <b>AuditService:</b> Records all operations with timestamp, user, device, action for traceability<br>• <b>DisassemblyStep:</b> Domain entity for each step (text instruction, image path, order number)<br>• <b>AuditLog:</b> Domain entity for operation tracking</p>
</details>

#### <a name="dm2"></a>  5.2 Dynamic Models
<details> 
    <summary> Workflow for BOM import and disassembly guidance </summary>
    <p><b>BOM Import Flow:</b> (1) User uploads Excel file → (2) BOMService parses via EPPlus → (3) Device, Component, Material entities created/updated → (4) Validation report returned to user<br><br><b>Disassembly Flow:</b> (1) Operator selects identified device → (2) DisassemblyService retrieves step list → (3) Frontend renders step with image and text → (4) Operator marks step complete → (5) Progress saved → (6) Next step displayed until completion.</p>
</details>
