using BomImportService.Interfaces;
using BomImportService.Models;

namespace BomImportService.Services;

public class EECClassifier : IEECClassifier
{
    private readonly IStrapiClient _strapiClient;

    public EECClassifier(IStrapiClient strapiClient)
    {
        _strapiClient = strapiClient;
    }

    public async Task<int> GetCategoryIdAsync(string designatorCode)
    {
        var url = $"/api/reference-designator?populate=eecCategory&filters[designatorCode][$eq]={Uri.EscapeDataString(designatorCode)}";
        var response = await _strapiClient.GetAsync<List<ReferenceDesignatorDto>>(url);

        return response.Data?.FirstOrDefault()?.EECCategoryId ?? 10;
    }
}
