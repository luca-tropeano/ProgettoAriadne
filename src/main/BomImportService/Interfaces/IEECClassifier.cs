namespace BomImportService.Interfaces;

public interface IEECClassifier
{
    Task<int> GetCategoryIdAsync(string designatorCode);
}
