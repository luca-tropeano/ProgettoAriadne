namespace BomImportService.Interfaces;

public interface IClaudeClient
{
    Task<string> SendMessageAsync(string userMessage, string? systemPrompt = null);
}
