using BomImportService.Models;

namespace BomImportService.Interfaces;

public interface IStrapiClient
{
    Task<ApiResponse<T>> GetAsync<T>(string endpoint, object? filters = null);
    Task<ApiResponse<T>> PostAsync<T>(string endpoint, object data);
    Task<ApiResponse<T>> PutAsync<T>(string endpoint, int id, object data);
    Task<bool> DeleteAsync(string endpoint, int id);
}
