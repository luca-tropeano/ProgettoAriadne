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

    public async Task<BomImportResult> ImportBomAsync(
        Stream excelStream,
        int deviceId,
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

        await _strapiClient.PostAsync<object>("/api/audit-logs", new
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

    private static BOMEntryDto? ParseRow(ExcelWorksheet ws, int row)
    {
        var reference = ws.Cells[row, 3].Text;
        if (string.IsNullOrWhiteSpace(reference)) return null;

        return new BOMEntryDto
        {
            ItemNumber = int.Parse(ws.Cells[row, 1].Text),
            Quantity = int.Parse(ws.Cells[row, 2].Text),
            ReferenceDesignator = reference,
            PartValue = ws.Cells[row, 4].Text,
            Manufacturer = ws.Cells[row, 6].Text,
            MountingType = DetectMountingType(ws.Cells[row, 5].Text),
            Device = 0 // da popolare dal chiamante
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
        int deviceId,
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

                await _strapiClient.PostAsync<BOMEntryDto>(
                    "/api/bom-entries",
                    new { data = entry });

                result.ImportedRows++;
            }
            catch (Exception ex)
            {
                result.FailedRows++;
                result.Errors.Add($"Componente {entry.ReferenceDesignator}: {ex.Message}");
            }
        }

        await _strapiClient.PostAsync<object>("/api/audit-logs", new
        {
            data = new
            {
                timestamp = DateTime.UtcNow,
                userId,
                action = "BOM_IMPORT_PDF",
                details = $"{result.ImportedRows} componenti importati da PDF via Claude",
                device = deviceId
            }
        });

        return result;
    }
}
