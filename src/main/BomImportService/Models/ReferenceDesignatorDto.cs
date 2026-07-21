using System.Text.Json.Serialization;

namespace BomImportService.Models;

public class ReferenceDesignatorDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("designatorCode")]
    public string? DesignatorCode { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("eecCategory")]
    public EECCategoryRef? EECCategory { get; set; }

    public int EECCategoryId => EECCategory?.Id ?? 10;
}

public class EECCategoryRef
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
}
