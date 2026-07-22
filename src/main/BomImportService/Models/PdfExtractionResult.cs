namespace BomImportService.Models;

public class PdfExtractionResult
{
    public bool Success => Errors.Count == 0 && ExtractedEntries.Count > 0;
    public List<BOMEntryDto> ExtractedEntries { get; set; } = [];
    public List<string> Errors { get; set; } = [];
    public List<string> Warnings { get; set; } = [];
    public string RawText { get; set; } = string.Empty;
}
