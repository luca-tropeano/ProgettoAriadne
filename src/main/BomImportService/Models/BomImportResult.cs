namespace BomImportService.Models;

public class BomImportResult
{
    public bool Success => FailedRows == 0;
    public int TotalRows => ImportedRows + FailedRows;
    public int ImportedRows { get; set; }
    public int FailedRows { get; set; }
    public List<string> Warnings { get; set; } = [];
    public List<string> Errors { get; set; } = [];
}
