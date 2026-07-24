# BOM Import Service — Specifica Tecnica

**VERSIONE: 1.4** | **Data:** 22/07/2026 | **Autore:** Tropeano Luca

## Panoramica

Servizio .NET/C# (CLI) per importare file BOM da Excel (.xlsx) e da PDF (via Claude AI), scrivendo i dati su Strapi tramite API REST.

**Flussi supportati:**
- **Excel (.xlsx)** → EPPlus parser → Strapi API → PostgreSQL
- **PDF (.pdf)** → PdfPig text extraction → Claude AI API → JSON → Strapi API → PostgreSQL

## Struttura del Progetto

```
BomImportService/
├── Program.cs                          # CLI entry point (auto-detect .pdf/.xlsx)
├── appsettings.json                    # Configurazione Strapi + Claude
├── BomImportService.csproj             # .NET 10, EPPlus, PdfPig, Hosting
├── Models/
│   ├── BOMEntryDto.cs                  # DTO riga BOM
│   ├── BomImportResult.cs              # Risultato import
│   ├── ClaudeConfig.cs                 # Config Claude API
│   ├── DeviceDto.cs                    # DTO dispositivo (brand, model, manufacturer, year)
│   ├── StrapiConfig.cs                 # Config Strapi
│   ├── ApiResponse.cs                  # Wrapper risposta Strapi
│   └── ReferenceDesignatorDto.cs       # DTO reference designator
├── Interfaces/
│   ├── IStrapiClient.cs               # Client HTTP Strapi
│   ├── IDesignatorValidator.cs        # Validatore designator
│   ├── IEECClassifier.cs             # Classificatore EEC
│   ├── IPdfExtractor.cs              # Estrattore testo PDF
│   └── IClaudeClient.cs              # Client API Claude
├── Services/
│   ├── StrapiClient.cs                # Implementazione HTTP Strapi
│   ├── DesignatorValidator.cs         # Mapping lettera → codice designator
│   ├── EECClassifier.cs              # Classificazione EEC da Strapi
│   ├── BOMImportService.cs           # Logica import Excel + entry list
│   ├── PdfExtractor.cs               # Estrazione testo da PDF (PdfPig)
│   └── ClaudeClient.cs               # Client API Claude (Anthropic)
└── Tests/
    └── BomImportService.Tests/        # Progetto xUnit (62 test)
        ├── DesignatorValidatorTests.cs
        ├── PdfExtractorTests.cs
        ├── BomEntryParsingTests.cs
        ├── ClaudeClientTests.cs
        └── ExcelParsingTests.cs
```

## Program.cs — CLI Entry Point

Auto-rileva il formato file (.pdf o .xlsx) e invoca il flusso appropriato. Supporta flag CLI per la creazione automatica dispositivi.

```csharp
var flags = ParseFlags(args);
var filePath = flags.TryGetValue("--file", out var fp) ? fp : args.FirstOrDefault(a => !a.StartsWith("--"));

// Device auto-creation from CLI flags
DeviceDto? deviceInfo = null;
if (flags.ContainsKey("--brand") || flags.ContainsKey("--model"))
{
    deviceInfo = new DeviceDto
    {
        Brand = flags.GetValueOrDefault("--brand", ""),
        ModelName = flags.GetValueOrDefault("--model", ""),
        Manufacturer = flags.GetValueOrDefault("--manufacturer", flags.GetValueOrDefault("--brand", "")),
        YearOfProduction = int.TryParse(flags.GetValueOrDefault("--year", ""), out var yr) ? yr : DateTime.Now.Year
    };
}

string? deviceDocId = null;
if (deviceInfo != null && !string.IsNullOrEmpty(deviceInfo.ModelName))
    deviceDocId = await importService.FindOrCreateDeviceAsync(deviceInfo);

switch (ext)
{
    case ".xlsx":
    case ".xls":
        await using (var stream = File.OpenRead(filePath))
        {
            var excelResult = await importService.ImportBomAsync(stream, deviceDocId, "cli");
            PrintResult(excelResult);
        }
        break;

    case ".pdf":
        var rawText = pdfExtractor.ExtractText(filePath);
        var claudeResponse = await claudeClient.SendMessageAsync(rawText, systemPrompt);
        var entries = ParseClaudeResponse(claudeResponse);
        var pdfResult = await importService.ImportBomFromEntriesAsync(entries, deviceDocId, "cli");
        PrintResult(pdfResult);
        break;
}
```

**Uso:**
```
BomImportService <file> [--brand X] [--model X] [--manufacturer X] [--year N]
```

## BOMImportService.cs

Punto di ingresso dell'import. Supporta due metodi:

```csharp
public class BOMImportService
{
    private readonly IStrapiClient _strapiClient;
    private readonly IDesignatorValidator _designatorValidator;
    private readonly IEECClassifier _eecClassifier;

    // Verifica se il dispositivo esiste, lo crea se non esiste → restituisce documentId
    public async Task<string?> FindOrCreateDeviceAsync(DeviceDto device);

    // Flusso Excel: stream → EPPlus → parsing righe → Strapi API
    public async Task<BomImportResult> ImportBomAsync(
        Stream excelStream, string? deviceDocumentId, string userId);

    // Flusso PDF: lista entries da Claude → validazione → Strapi API
    public async Task<BomImportResult> ImportBomFromEntriesAsync(
        List<BOMEntryDto> entries, string? deviceDocumentId, string userId);
}
```

**Logica condivisa (entrambi i flussi):**
1. Per ogni entry: `DesignatorValidator.GetDesignatorCode()` → codice designator
2. `EECClassifier.GetCategoryIdAsync()` → categoria EEC da Strapi
3. Costruzione payload con `{ data = { ...entry, device = { documentId = ... } } }` (Strapi v5 relations)
4. `StrapiClient.PostAsync("/api/bom-entry", payload)` → salvataggio
5. Audit log → `POST /api/audit-log` (con device relation via documentId)

### Rilevamento MountingType (SMT/THT)

```csharp
private static string DetectMountingType(string package)
{
    var upper = package.Trim().ToUpperInvariant();
    if (upper.StartsWith("DIP") || upper.StartsWith("SIP") || upper.StartsWith("TO-"))
        return "THT";
    return "SMT";
}
```

## PdfExtractor.cs

Estrae testo da PDF tramite PdfPig (OpenSource, nessuna dipendenza esterna).

```csharp
public class PdfExtractor : IPdfExtractor
{
    public string ExtractText(string pdfPath) { ... }
    public string ExtractText(Stream pdfStream)
    {
        using var document = PdfDocument.Open(pdfStream);
        var sb = new StringBuilder();
        foreach (var page in document.GetPages())
        {
            sb.AppendLine($"--- Page {page.Number} ---");
            sb.AppendLine(page.Text);
        }
        return sb.ToString();
    }
}
```

**Note:**
- Funziona solo con PDF testuali (non scansionati/immagini)
- Per PDF scannerizzati è necessario un passaggio OCR (fase futura)

## ClaudeClient.cs

Client HTTP per l'API Claude (Anthropic). Utilizzato per estrarre dati BOM da testo PDF non strutturato.

```csharp
public class ClaudeClient : IClaudeClient
{
    private readonly HttpClient _httpClient;
    private readonly ClaudeConfig _config;

    public ClaudeClient(ClaudeConfig config)
    {
        _httpClient = new HttpClient { BaseAddress = new Uri(config.BaseUrl) };
        _httpClient.DefaultRequestHeaders.Add("x-api-key", config.ApiKey);
        _httpClient.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
    }

    public async Task<string> SendMessageAsync(string userMessage, string? systemPrompt = null);
}
```

**System Prompt predefinito (Program.cs):**
```
You are a BOM (Bill of Materials) extraction assistant.
Extract component data from the provided text and return ONLY a JSON array.
Each object must have: itemNumber, quantity, referenceDesignator, partValue,
manufacturer, manufacturerOrderCode, mountingType ("SMT"/"THT").
Rules: default SMT if unknown, return ONLY JSON array, null for unknown fields.
```

### ClaudeConfig (appsettings.json)

```json
{
  "Claude": {
    "ApiKey": "<your-anthropic-api-key>",
    "Model": "claude-sonnet-4-20250514",
    "BaseUrl": "https://api.anthropic.com",
    "MaxTokens": 4096
  }
}
```

## DTOs

```csharp
public class BOMEntryDto
{
    public int ItemNumber { get; set; }
    public int Quantity { get; set; }
    public string ReferenceDesignator { get; set; } = string.Empty;
    public string? MountingType { get; set; }
    public string? PartValue { get; set; }
    public string? Manufacturer { get; set; }
    public string? ManufacturerOrderCode { get; set; }
    public string? Supplier1 { get; set; }
    public string? Supplier1OrderCode { get; set; }
    public string? Supplier2 { get; set; }
    public string? Supplier2OrderCode { get; set; }
    public string? Supplier3 { get; set; }
    public string? Supplier3OrderCode { get; set; }
    public string? DesignatorCode { get; set; }
    public int EECCategoryId { get; set; }
    public int Device { get; set; }
    public string? Notes { get; set; }
}

public class BomImportResult
{
    public bool Success => FailedRows == 0;
    public int TotalRows => ImportedRows + FailedRows;
    public int ImportedRows { get; set; }
    public int FailedRows { get; set; }
    public List<string> Warnings { get; set; } = new();
    public List<string> Errors { get; set; } = new();
}

public class ClaudeConfig
{
    public string ApiKey { get; set; } = string.Empty;
    public string Model { get; set; } = "claude-sonnet-4-20250514";
    public string BaseUrl { get; set; } = "https://api.anthropic.com";
    public int MaxTokens { get; set; } = 4096;
}

public class DeviceDto
{
    public string Brand { get; set; } = string.Empty;
    public string ModelName { get; set; } = string.Empty;
    public string Manufacturer { get; set; } = string.Empty;
    public int YearOfProduction { get; set; }
    public string? Notes { get; set; }
}
```

## EECClassifier

Mappa designator → categoria EEC tramite query Strapi:

```csharp
public class EECClassifier : IEECClassifier
{
    public async Task<int> GetCategoryIdAsync(string designatorCode)
    {
        var url = $"/api/reference-designator?populate=eecCategory&filters[designatorCode][$eq]={Uri.EscapeDataString(designatorCode)}";
        var response = await _strapiClient.GetAsync<List<ReferenceDesignatorDto>>(url);
        return response.Data?.FirstOrDefault()?.EECCategoryId ?? 10;
    }
}
```

**Note:**
- Usa query string diretta `filters[designatorCode][$eq]=X` (non serializzazione oggetti annidati)
- `populate=eecCategory` per includere la relazione nella risposta
- Default: categoria 10 (Resistors) se non trovata

## DesignatorValidator

Mapping lettera iniziale → codice designator (IEEE/ANSI):

```csharp
private static readonly Dictionary<char, string> PrefixMap = new()
{
    { 'R', "R" }, { 'C', "C" }, { 'L', "L" }, { 'D', "D" },
    { 'Q', "Q" }, { 'U', "U" }, { 'J', "J" }, { 'P', "P" },
    { 'X', "X" }, { 'Y', "Y" }, { 'S', "SW" },
    { 'F', "F" }, { 'T', "T" }, { 'K', "K" }, { 'M', "M" },
    { 'B', "B" }, { 'Z', "Z" }, { 'A', "ANT" }, { 'H', "H" },
};
```

## Diagramma di Sequenza — Flusso Excel

```
Utente               Program.cs          BOMImportService     EPPlus      StrapiClient    Strapi API
  │                      │                      │                │              │              │
  │──xlsx path──────────▶│                      │                │              │              │
  │                      │──ImportBomAsync()───▶│                │              │              │
  │                      │                      │──Read worksheet▶              │              │
  │                      │                      │◀────rows───────│              │              │
  │                      │                      │                               │              │
  │                      │                      │──GetDesignatorCode()          │              │
  │                      │                      │──GetCategoryIdAsync()──────────────────────▶│
  │                      │                      │◀─────────────────────────────────────────────│
  │                      │                      │                               │              │
  │                      │                      │──PostAsync(/api/bom-entry)──────────────▶│
  │                      │                      │◀─────────────────────────────────────────────│
  │                      │◀──BomImportResult────│                               │              │
```

## Diagramma di Sequenza — Flusso PDF → Claude

```
Utente               Program.cs     PdfExtractor   ClaudeClient    BOMImportService    Strapi API
  │                      │               │              │                 │                │
  │──pdf path───────────▶│               │              │                 │                │
  │                      │──ExtractText()▶              │                 │                │
  │                      │◀──raw text────│              │                 │                │
  │                      │                              │                 │                │
  │                      │──SendMessageAsync(rawText)──▶│                 │                │
  │                      │◀──JSON response─────────────│                 │                │
  │                      │                              │                 │                │
  │                      │──ParseClaudeResponse()───────│                 │                │
  │                      │                              │                 │                │
  │                      │──ImportBomFromEntriesAsync(entries)──────────▶│                │
  │                      │                              │                 │──POST─────────▶│
  │                      │◀──BomImportResult────────────────────────────│                │
```

## Excel Column Mapping (17-colonne)

La BOM Excel reale (`Scheda STM-Steval Spin3204 - Copia x Luca.xlsx`) ha **17 colonne** con intestazioni alla riga 6:

| Col | Header | Campo Strapi | Metodo parsing |
|-----|--------|-------------|----------------|
| 1 | Item | itemNumber | `int.TryParse` — salta righe non numeriche |
| 2 | Qty | quantity | `int.TryParse` |
| 3 | Reference | referenceDesignator | Testo diretto |
| 5 | Part/Value | partValue | Testo diretto |
| 9 | Package | mountingType | `DetectMountingType()` — DIP/SIP/TO- → THT, altrimenti SMT |
| 10 | Manufacturer | manufacturer | Testo diretto |
| 11 | Mfr Order Code | manufacturerOrderCode | Testo diretto |
| 12 | Notes | notes | Testo diretto |
| 13 | Supplier | supplier1 | Testo diretto |
| 14 | Supplier Code | supplier1OrderCode | Testo diretto |

Colonne 4 (Description), 6 (Footprint), 7 (Qty Stock), 8 (Unit Price), 15-17 (extra supplier) non mappate.

## NuGet Dependencies

```xml
<PackageReference Include="EPPlus" Version="7.6.1" />
<PackageReference Include="PdfPig" Version="0.1.10" />
<PackageReference Include="Microsoft.Extensions.Configuration.Binder" Version="10.0.0" />
<PackageReference Include="Microsoft.Extensions.Hosting" Version="10.0.0" />
<PackageReference Include="Microsoft.Extensions.Http" Version="10.0.0" />
```

## Configurazione (appsettings.json)

```json
{
  "Strapi": {
    "BaseUrl": "http://localhost:1337",
    "ApiToken": ""
  },
  "Claude": {
    "ApiKey": "<your-anthropic-api-key>",
    "Model": "claude-sonnet-4-20250514",
    "BaseUrl": "https://api.anthropic.com",
    "MaxTokens": 4096
  }
}
```

**Note:** `ApiToken` è opzionale — se vuoto o inizia con `<`, lo StrapiClient si affida ai permessi CRUD del ruolo Public configurati dal bootstrap. `ApiKey` è obbligatorio per l'estrazione PDF→Claude.

## Progetto Test (xUnit)

Progetto `BomImportService.Tests` con **62 test** coprenti:

| Classe Test | # Test | Cosa verifica |
|------------|--------|---------------|
| DesignatorValidatorTests | 10 | Mapping designator → codice (R, C, U, S→SW, multi-char) |
| PdfExtractorTests | 4 | Estrazione testo da PDF, file non esistente, stream vs file |
| BomEntryParsingTests | 9 | Parsing Excel rows, mounting type detection, validazione |
| ClaudeClientTests | 7 | Serializzazione request, deserializzazione response, errori API |
| ExcelParsingTests | 4 | Lettura Excel reale, parsing righe BOM, righe vuote |

Esecuzione:
```bash
dotnet test src/tests/BomImportService.Tests/ --verbosity minimal
```
