using System.Text.Json;
using BomImportService.Interfaces;
using BomImportService.Models;
using OfficeOpenXml;

namespace BomImportService.Services;

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

    public async Task<string?> FindOrCreateDeviceAsync(DeviceDto device)
    {
        var response = await _strapiClient.GetAsync<List<JsonElement>>(
            $"/api/device?filters[modelName][$eq]={Uri.EscapeDataString(device.ModelName)}");
        var existing = response.Data;
        if (existing != null && existing.Count > 0 && existing[0].ValueKind == JsonValueKind.Object
            && existing[0].TryGetProperty("documentId", out var docId))
        {
            Console.WriteLine($"  Device found: {existing[0].GetProperty("modelName").GetString()} (id={existing[0].GetProperty("id").GetInt32()})");
            return docId.GetString();
        }

        Console.WriteLine($"  Creating device: {device.Brand} {device.ModelName}...");
        var result = await _strapiClient.PostAsync<JsonElement>("/api/device", new
        {
            data = new
            {
                device.Brand,
                device.ModelName,
                device.Manufacturer,
                device.YearOfProduction,
                device.Notes
            }
        });
        var id = result.Data.ValueKind == JsonValueKind.Object
            && result.Data.TryGetProperty("documentId", out var newDocId)
            ? newDocId.GetString() : null;
        Console.WriteLine($"  Device created: {device.ModelName} (docId={id})");
        return id;
    }

    public async Task<BomImportResult> ImportBomAsync(
        Stream excelStream,
        string? deviceDocumentId,
        string userId)
    {
        var result = new BomImportResult();

        using var package = new ExcelPackage(excelStream);
        var worksheet = package.Workbook.Worksheets[0];
        int rowCount = worksheet.Dimension.Rows;

        for (int row = 2; row <= rowCount; row++)
        {
            try
            {
                var entry = ParseRow(worksheet, row);
                if (entry == null) continue;

                entry.DesignatorCode =
                    _designatorValidator.GetDesignatorCode(entry.ReferenceDesignator);

                entry.EECCategoryId =
                    await _eecClassifier.GetCategoryIdAsync(entry.DesignatorCode);

                var payload = new
                {
                    data = new
                    {
                        entry.ItemNumber,
                        entry.Quantity,
                        entry.ReferenceDesignator,
                        entry.MountingType,
                        entry.PartValue,
                        entry.Manufacturer,
                        entry.ManufacturerOrderCode,
                        entry.Supplier1,
                        entry.Supplier1OrderCode,
                        entry.Supplier2,
                        entry.Supplier2OrderCode,
                        entry.Supplier3,
                        entry.Supplier3OrderCode,
                        entry.DesignatorCode,
                        entry.Notes,
                        device = deviceDocumentId != null ? new { documentId = deviceDocumentId } : null
                    }
                };

                await _strapiClient.PostAsync<BOMEntryDto>(
                    "/api/bom-entry",
                    payload);

                result.ImportedRows++;
            }
            catch (Exception ex)
            {
                result.FailedRows++;
                result.Errors.Add($"Riga {row}: {ex.Message}");
            }
        }

        await _strapiClient.PostAsync<object>("/api/audit-log", new
        {
            data = new
            {
                timestamp = DateTime.UtcNow,
                userId,
                action = "BOM_IMPORT",
                details = $"{result.ImportedRows} componenti importati",
                device = deviceDocumentId != null ? new { documentId = deviceDocumentId } : null
            }
        });

        return result;
    }

    private static BOMEntryDto? ParseRow(ExcelWorksheet ws, int row)
    {
        var itemText = ws.Cells[row, 1].Text;
        if (string.IsNullOrWhiteSpace(itemText)) return null;
        if (!int.TryParse(itemText, out var itemNumber)) return null;

        var quantityText = ws.Cells[row, 2].Text;
        if (!int.TryParse(quantityText, out var quantity)) return null;

        var reference = ws.Cells[row, 3].Text;
        if (string.IsNullOrWhiteSpace(reference)) return null;

        return new BOMEntryDto
        {
            ItemNumber = itemNumber,
            Quantity = quantity,
            ReferenceDesignator = reference,
            PartValue = ws.Cells[row, 5].Text,
            Manufacturer = ws.Cells[row, 10].Text,
            ManufacturerOrderCode = ws.Cells[row, 11].Text,
            Supplier1 = ws.Cells[row, 13].Text,
            Supplier1OrderCode = ws.Cells[row, 14].Text,
            Notes = ws.Cells[row, 12].Text,
            MountingType = DetectMountingType(ws.Cells[row, 9].Text),
        };
    }

    private static string DetectMountingType(string package)
    {
        var upper = package.Trim().ToUpperInvariant();
        if (upper.StartsWith("DIP") || upper.StartsWith("SIP") || upper.StartsWith("TO-"))
            return "THT";
        return "SMT";
    }

    public async Task<BomImportResult> ImportBomFromEntriesAsync(
        List<BOMEntryDto> entries,
        string? deviceDocumentId,
        string userId)
    {
        var result = new BomImportResult();

        foreach (var entry in entries)
        {
            try
            {
                entry.DesignatorCode ??=
                    _designatorValidator.GetDesignatorCode(entry.ReferenceDesignator);

                entry.EECCategoryId =
                    await _eecClassifier.GetCategoryIdAsync(entry.DesignatorCode);

                var payload = new
                {
                    data = new
                    {
                        entry.ItemNumber,
                        entry.Quantity,
                        entry.ReferenceDesignator,
                        entry.MountingType,
                        entry.PartValue,
                        entry.Manufacturer,
                        entry.ManufacturerOrderCode,
                        entry.Supplier1,
                        entry.Supplier1OrderCode,
                        entry.Supplier2,
                        entry.Supplier2OrderCode,
                        entry.Supplier3,
                        entry.Supplier3OrderCode,
                        entry.DesignatorCode,
                        entry.Notes,
                        device = deviceDocumentId != null ? new { documentId = deviceDocumentId } : null
                    }
                };

                await _strapiClient.PostAsync<BOMEntryDto>(
                    "/api/bom-entry",
                    payload);

                result.ImportedRows++;
            }
            catch (Exception ex)
            {
                result.FailedRows++;
                result.Errors.Add($"Componente {entry.ReferenceDesignator}: {ex.Message}");
            }
        }

        await _strapiClient.PostAsync<object>("/api/audit-log", new
        {
            data = new
            {
                timestamp = DateTime.UtcNow,
                userId,
                action = "BOM_IMPORT_PDF",
                details = $"{result.ImportedRows} componenti importati da PDF",
                device = deviceDocumentId != null ? new { documentId = deviceDocumentId } : null
            }
        });

        return result;
    }
}
