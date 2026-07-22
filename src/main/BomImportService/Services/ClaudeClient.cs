using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using BomImportService.Interfaces;
using BomImportService.Models;

namespace BomImportService.Services;

public class ClaudeClient : IClaudeClient
{
    private readonly HttpClient _httpClient;
    private readonly ClaudeConfig _config;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true
    };

    public ClaudeClient(ClaudeConfig config)
    {
        _config = config;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(config.BaseUrl.TrimEnd('/'))
        };
        _httpClient.DefaultRequestHeaders.Add("x-api-key", config.ApiKey);
        _httpClient.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
    }

    public async Task<string> SendMessageAsync(string userMessage, string? systemPrompt = null)
    {
        var messages = new List<ClaudeMessage>
        {
            new() { Role = "user", Content = userMessage }
        };

        var requestBody = new ClaudeRequest
        {
            Model = _config.Model,
            MaxTokens = _config.MaxTokens,
            Messages = messages
        };

        if (!string.IsNullOrEmpty(systemPrompt))
        {
            requestBody.System = systemPrompt;
        }

        var json = JsonSerializer.Serialize(requestBody, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync("/v1/messages", content);
        var responseContent = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException(
                $"Claude API error {(int)response.StatusCode}: {responseContent}");
        }

        var claudeResponse = JsonSerializer.Deserialize<ClaudeResponse>(responseContent, JsonOptions)
            ?? throw new InvalidOperationException("Empty Claude API response");

        return claudeResponse.Content?.FirstOrDefault()?.Text
            ?? throw new InvalidOperationException("No text in Claude response");
    }
}

#region Claude API Models

public class ClaudeRequest
{
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; } = 4096;

    [JsonPropertyName("messages")]
    public List<ClaudeMessage> Messages { get; set; } = [];

    [JsonPropertyName("system")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? System { get; set; }
}

public class ClaudeMessage
{
    [JsonPropertyName("role")]
    public string Role { get; set; } = "user";

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}

public class ClaudeResponse
{
    [JsonPropertyName("content")]
    public List<ClaudeContent>? Content { get; set; }

    [JsonPropertyName("error")]
    public ClaudeError? Error { get; set; }
}

public class ClaudeContent
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;
}

public class ClaudeError
{
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    [JsonPropertyName("message")]
    public string? Message { get; set; }
}

#endregion
