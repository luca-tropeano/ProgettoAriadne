# BOM Import Service — Specifica Tecnica

## Panoramica

Servizio .NET/C# per importare file BOM Excel e scrivere i dati su Strapi tramite API REST.

## Struttura a Classi

### BOMImportService.cs

Punto di ingresso dell'import.

```csharp
public class BOMImportService
{
    private readonly IStrapiClient _strapiClient;
    private readonly IDesignatorValidator _designatorValidator;
    private readonly IEECClassifier _eecClassifier;

    public BOMImportService(
        IStrapiClient strapiClient,
        IDesignatorValidator designatorValidator,
        IEECClassifier eecClassifier)
    {
        _strapiClient = strapiClient;
        _designatorValidator = designatorValidator;
        _eecClassifier = eecClassifier;
    }

    public async Task<BomImportResult> ImportBomAsync(
        Stream excelStream,
        int deviceId,
        string userId)
    {
        var result = new BomImportResult();

        using var package = new ExcelPackage(excelStream);
        var worksheet = package.Workbook.Worksheets[0];
        int rowCount = worksheet.Dimension.Rows;

        // Salta header (riga 1)
        for (int row = 2; row <= rowCount; row++)
        {
            try
            {
                var entry = ParseRow(worksheet, row);
                if (entry == null) continue;

                // Determina designator code
                entry.DesignatorCode =
                    _designatorValidator.GetDesignatorCode(entry.ReferenceDesignator);

                // Ottieni EEC category
                entry.EECCategoryId =
                    await _eecClassifier.GetCategoryIdAsync(entry.DesignatorCode);

                // Invia a Strapi
                var response = await _strapiClient.PostAsync<BOMEntryDto>(
                    "/api/bom-entries",
                    new { data = entry });

                result.ImportedRows++;
            }
            catch (Exception ex)
            {
                result.FailedRows++;
                result.Errors.Add($"Riga {row}: {ex.Message}");
            }
        }

        // Log operazione
        await _strapiClient.PostAsync("/api/audit-logs", new
        {
            data = new
            {
                timestamp = DateTime.UtcNow,
                userId,
                action = "BOM_IMPORT",
                details = $"{result.ImportedRows} componenti importati",
                device = deviceId
            }
        });

        return result;
    }

    private BOMEntryDto? ParseRow(ExcelWorksheet ws, int row)
    {
        string? reference = ws.Cells[row, 3].Text;
        if (string.IsNullOrWhiteSpace(reference)) return null;

        return new BOMEntryDto
        {
            ItemNumber = int.Parse(ws.Cells[row, 1].Text),
            Quantity = int.Parse(ws.Cells[row, 2].Text),
            ReferenceDesignator = reference,
            PartValue = ws.Cells[row, 4].Text,
            Manufacturer = ws.Cells[row, 6].Text,
            MountingType = DetectMountingType(ws.Cells[row, 5].Text),
            Device = ws.Cells[row, 0].Text // da passare al chiamante
        };
    }

    private string DetectMountingType(string package)
    {
        // Package SMT: 0603, 0805, SOD123, SOT23, QFP, QFN...
        // Package THT: DIP, SIP, TO-220...
        return package.StartsWithAny("DIP", "SIP", "TO-") ? "THT" : "SMT";
    }
}
```

### DTOs

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
```

### IStrapiClient.cs

```csharp
public interface IStrapiClient
{
    Task<ApiResponse<T>> GetAsync<T>(string endpoint, object? filters = null);
    Task<ApiResponse<T>> PostAsync<T>(string endpoint, object data);
    Task<ApiResponse<T>> PutAsync<T>(string endpoint, int id, object data);
    Task<bool> DeleteAsync(string endpoint, int id);
}

public class StrapiClient : IStrapiClient
{
    private readonly HttpClient _httpClient;

    public StrapiClient(string baseUrl, string apiToken)
    {
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(baseUrl)
        };
        _httpClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", apiToken);
    }

    public async Task<ApiResponse<T>> GetAsync<T>(string endpoint, object? filters = null)
    {
        var queryString = filters?.ToQueryString() ?? "";
        var response = await _httpClient.GetAsync($"{endpoint}{queryString}");
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ApiResponse<T>>(content);
    }

    public async Task<ApiResponse<T>> PostAsync<T>(string endpoint, object data)
    {
        var json = JsonSerializer.Serialize(data);
        var httpContent = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync(endpoint, httpContent);
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ApiResponse<T>>(content);
    }

    // PUT, DELETE analoghi...
}

public class ApiResponse<T>
{
    public T Data { get; set; }
    public Error? Error { get; set; }
}
```

### IDesignatorValidator.cs

```csharp
public interface IDesignatorValidator
{
    string GetDesignatorCode(string referenceDesignator);
}

public class DesignatorValidator : IDesignatorValidator
{
    private static readonly Dictionary<char, string> PrefixMap = new()
    {
        { 'R', "R" }, { 'C', "C" }, { 'L', "L" }, { 'D', "D" },
        { 'Q', "Q" }, { 'U', "U" }, { 'J', "J" }, { 'P', "P" },
        { 'X', "X" }, { 'Y', "Y" }, { 'S', "SW" },
        { 'F', "F" }, { 'T', "T" }, { 'K', "K" }, { 'M', "M" },
        { 'B', "B" }, { 'Z', "Z" }, { 'A', "ANT" }, { 'H', "H" },
    };

    public string GetDesignatorCode(string reference)
    {
        if (string.IsNullOrWhiteSpace(reference))
            return "UNKNOWN";

        // Estrai prefisso letterale (es. "C1,C5" -> "C", "SW1" -> "SW")
        var first = reference.Trim().ToUpper()[0];

        if (PrefixMap.TryGetValue(first, out var code))
            return code;

        // Gestisci multi-carattere (SW, TVS, TH, REG, PS...)
        var prefix = reference.Trim().ToUpper();
        foreach (var kvp in PrefixMap.Where(k => k.Value.Length > 1)
                     .OrderByDescending(k => k.Value.Length))
        {
            if (prefix.StartsWith(kvp.Value))
                return kvp.Value;
        }

        return "UNKNOWN";
    }
}
```

### IEECClassifier.cs

```csharp
public interface IEECClassifier
{
    Task<int> GetCategoryIdAsync(string designatorCode);
}

public class EECClassifier : IEECClassifier
{
    private readonly IStrapiClient _strapiClient;

    public EECClassifier(IStrapiClient strapiClient)
    {
        _strapiClient = strapiClient;
    }

    public async Task<int> GetCategoryIdAsync(string designatorCode)
    {
        var response = await _strapiClient.GetAsync<ReferenceDesignatorDto>(
            "/api/reference-designators",
            new { filters = new { designatorCode = new { $eq = designatorCode } } });

        return response.Data?.EECCategoryId ?? 12; // default Resistors
    }
}
```

## Diagramma di Sequenza

```
Utente               BOMImportService          EPPlus            StrapiClient        Strapi API
  │                        │                     │                   │                  │
  │──Upload BOM.xlsx──────▶│                     │                   │                  │
  │                        │──Read worksheet────▶│                   │                  │
  │                        │◀─────rows───────────│                   │                  │
  │                        │                                              │
  │                        │──(per ogni riga)──────────────────────────────────────────▶│
  │                        │                              │                              │
  │                        │──GetDesignatorCode────┐       │                              │
  │                        │◀─────────────────────│       │                              │
  │                        │                              │                              │
  │                        │──GetCategoryIdAsync─────────────────────▶│──GET /api/ref-──▶│
  │                        │◀─────────────────────────────────────────│◀─────response────│
  │                        │                              │                              │
  │                        │──PostAsync(BOMEntry)──────────────────────▶│──POST /api/───▶│
  │                        │◀──────────────────────────────────────────│◀─────response──│
  │                        │                              │                              │
  │◀──────risultato────────│                              │                              │
```

## NuGet Dependencies

```xml
<PackageReference Include="EPPlus" Version="7.0+" />
<PackageReference Include="System.Text.Json" Version="8.0+" />
```

## Configurazione (appsettings.json)

```json
{
  "Strapi": {
    "BaseUrl": "http://localhost:1337",
    "ApiToken": "<your-api-token>"
  }
}
```
