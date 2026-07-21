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
        var response = await _strapiClient.GetAsync<ApiResponse<List<ReferenceDesignatorDto>>>(
            "/api/reference-designators",
            new { filters = new { designatorCode = new { eq = designatorCode } } });

        var designator = response.Data?.Data?.FirstOrDefault();
        return designator?.EECCategoryId ?? 10; // default Resistors
    }
}
