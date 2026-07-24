namespace BomImportService.Models;

public class DeviceDto
{
    public string Brand { get; set; } = string.Empty;
    public string ModelName { get; set; } = string.Empty;
    public string Manufacturer { get; set; } = string.Empty;
    public int YearOfProduction { get; set; }
    public string? Notes { get; set; }
}
