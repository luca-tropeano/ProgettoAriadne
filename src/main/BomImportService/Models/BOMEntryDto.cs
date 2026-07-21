namespace BomImportService.Models;

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
