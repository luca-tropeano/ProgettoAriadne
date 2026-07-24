using System.Text.Json;
using BomImportService.Models;
using BomImportService.Services;

namespace BomImportService.Tests;

public class ClaudeClientTests
{
    [Fact]
    public void ClaudeRequest_SerializesCorrectly()
    {
        var request = new ClaudeRequest
        {
            Model = "claude-sonnet-4-20250514",
            MaxTokens = 4096,
            Messages = [new() { Role = "user", Content = "Hello" }],
            System = "You are a test bot"
        };

        var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        Assert.Contains("\"model\":\"claude-sonnet-4-20250514\"", json);
        Assert.Contains("\"max_tokens\":4096", json);
        Assert.Contains("\"system\":\"You are a test bot\"", json);
        Assert.Contains("\"role\":\"user\"", json);
    }

    [Fact]
    public void ClaudeRequest_WithoutSystem_OmitsNull()
    {
        var request = new ClaudeRequest
        {
            Model = "claude-sonnet-4-20250514",
            MaxTokens = 1024,
            Messages = [new() { Role = "user", Content = "test" }]
        };

        var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
        });

        Assert.DoesNotContain("system", json);
    }

    [Fact]
    public void ClaudeResponse_DeserializesCorrectly()
    {
        var json = """
        {
            "content": [
                {"type": "text", "text": "[{\"itemNumber\":1}]"}
            ]
        }
        """;

        var response = JsonSerializer.Deserialize<ClaudeResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        Assert.NotNull(response);
        Assert.NotNull(response.Content);
        Assert.Single(response.Content);
        Assert.Equal("[{\"itemNumber\":1}]", response.Content[0].Text);
    }

    [Fact]
    public void ClaudeResponse_WithError_ParsesError()
    {
        var json = """
        {
            "error": {
                "type": "invalid_request_error",
                "message": "Invalid API key"
            }
        }
        """;

        var response = JsonSerializer.Deserialize<ClaudeResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        Assert.NotNull(response);
        Assert.NotNull(response.Error);
        Assert.Equal("invalid_request_error", response.Error.Type);
        Assert.Equal("Invalid API key", response.Error.Message);
    }

    [Fact]
    public void ClaudeConfig_DefaultValues()
    {
        var config = new ClaudeConfig();
        Assert.Equal("claude-sonnet-4-20250514", config.Model);
        Assert.Equal("https://api.anthropic.com", config.BaseUrl);
        Assert.Equal(4096, config.MaxTokens);
        Assert.Equal(string.Empty, config.ApiKey);
    }

    [Fact]
    public void StrapiConfig_DefaultValues()
    {
        var config = new StrapiConfig();
        Assert.Equal("http://localhost:1337", config.BaseUrl);
        Assert.Equal(string.Empty, config.ApiToken);
    }
}
