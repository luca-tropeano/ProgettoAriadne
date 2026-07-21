using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using BomImportService.Interfaces;
using BomImportService.Models;

namespace BomImportService.Services;

public class StrapiClient : IStrapiClient
{
    private readonly HttpClient _httpClient;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true
    };

    public StrapiClient(string baseUrl, string apiToken)
    {
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(baseUrl.TrimEnd('/'))
        };
        _httpClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", apiToken);
    }

    public async Task<ApiResponse<T>> GetAsync<T>(string endpoint, object? filters = null)
    {
        var queryString = filters?.ToQueryString() ?? "";
        var response = await _httpClient.GetAsync($"{endpoint}?{queryString}");
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ApiResponse<T>>(content, JsonOptions)
            ?? throw new InvalidOperationException("Empty API response");
    }

    public async Task<ApiResponse<T>> PostAsync<T>(string endpoint, object data)
    {
        var json = JsonSerializer.Serialize(new { data }, JsonOptions);
        var httpContent = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync(endpoint, httpContent);
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ApiResponse<T>>(content, JsonOptions)
            ?? throw new InvalidOperationException("Empty API response");
    }

    public async Task<ApiResponse<T>> PutAsync<T>(string endpoint, int id, object data)
    {
        var json = JsonSerializer.Serialize(new { data }, JsonOptions);
        var httpContent = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PutAsync($"{endpoint}/{id}", httpContent);
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ApiResponse<T>>(content, JsonOptions)
            ?? throw new InvalidOperationException("Empty API response");
    }

    public async Task<bool> DeleteAsync(string endpoint, int id)
    {
        var response = await _httpClient.DeleteAsync($"{endpoint}/{id}");
        return response.IsSuccessStatusCode;
    }
}

public static class QueryStringExtensions
{
    public static string ToQueryString(this object filters)
    {
        var json = JsonSerializer.Serialize(filters, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        using var doc = JsonDocument.Parse(json);
        var sb = new StringBuilder();

        foreach (var property in doc.RootElement.EnumerateObject())
        {
            if (sb.Length > 0)
                sb.Append('&');
            sb.Append(Uri.EscapeDataString(property.Name));
            sb.Append('=');
            sb.Append(Uri.EscapeDataString(property.Value.ToString()));
        }

        return sb.ToString();
    }
}
