using BomImportService.Interfaces;
using BomImportService.Models;
using BomImportService.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = Host.CreateDefaultBuilder(args)
    .ConfigureServices((context, services) =>
    {
        var strapiConfig = context.Configuration.GetSection("Strapi").Get<StrapiConfig>()
            ?? throw new InvalidOperationException("Strapi config not found");

        var claudeConfig = context.Configuration.GetSection("Claude").Get<ClaudeConfig>()
            ?? throw new InvalidOperationException("Claude config not found");

        services.AddSingleton<IStrapiClient>(_ =>
            new StrapiClient(strapiConfig.BaseUrl, strapiConfig.ApiToken));
        services.AddSingleton<IDesignatorValidator, DesignatorValidator>();
        services.AddSingleton<IEECClassifier, EECClassifier>();
        services.AddSingleton<IPdfExtractor, PdfExtractor>();
        services.AddSingleton<IClaudeClient>(_ => new ClaudeClient(claudeConfig));
        services.AddSingleton<BOMImportService>();
    })
    .Build();

var importService = host.Services.GetRequiredService<BOMImportService>();
var pdfExtractor = host.Services.GetRequiredService<IPdfExtractor>();
var claudeClient = host.Services.GetRequiredService<IClaudeClient>();

if (args.Length == 0)
{
    Console.WriteLine("Usage: BomImportService <path-to-file>");
    Console.WriteLine("  .xlsx  — import diretto da Excel");
    Console.WriteLine("  .pdf   — estrazione via Claude AI → Strapi");
    return;
}

var filePath = args[0];
var ext = Path.GetExtension(filePath).ToLowerInvariant();

switch (ext)
{
    case ".xlsx":
    case ".xls":
        Console.WriteLine($"Import Excel: {filePath}");
        await using (var stream = File.OpenRead(filePath))
        {
            var excelResult = await importService.ImportBomAsync(stream, deviceId: 1, userId: "cli");
            PrintResult(excelResult);
        }
        break;

    case ".pdf":
        Console.WriteLine($"Estrazione PDF: {filePath}");
        Console.WriteLine("Reading PDF text...");
        var rawText = pdfExtractor.ExtractText(filePath);

        if (string.IsNullOrWhiteSpace(rawText))
        {
            Console.Error.WriteLine("No text extracted from PDF. The file may be a scanned image.");
            return;
        }

        Console.WriteLine($"Extracted {rawText.Length} characters from PDF.");
        Console.WriteLine("Sending to Claude AI for BOM extraction...");

        var systemPrompt = """
            You are a BOM (Bill of Materials) extraction assistant.
            Extract component data from the provided text and return ONLY a JSON array.
            Each object must have these fields:
            - itemNumber: int (row number)
            - quantity: int
            - referenceDesignator: string (e.g. "C1,C5,C7")
            - partValue: string or null
            - manufacturer: string or null
            - manufacturerOrderCode: string or null
            - mountingType: "SMT" or "THT" (detect from package type)
            
            Rules:
            - If mounting type cannot be determined, default to "SMT"
            - Return ONLY the JSON array, no explanation, no markdown
            - If a field is unknown, use null
            """;

        var claudeResponse = await claudeClient.SendMessageAsync(rawText, systemPrompt);

        Console.WriteLine("Parsing Claude response...");
        var entries = ParseClaudeResponse(claudeResponse);

        Console.WriteLine($"Extracted {entries.Count} components from PDF.");
        Console.WriteLine("Importing to Strapi...");

        var pdfResult = await importService.ImportBomFromEntriesAsync(entries, deviceId: 1, userId: "cli");
        PrintResult(pdfResult);
        break;

    default:
        Console.Error.WriteLine($"Unsupported file format: {ext}");
        Console.WriteLine("Supported formats: .xlsx, .xls, .pdf");
        break;
}

static List<BOMEntryDto> ParseClaudeResponse(string response)
{
    var json = response.Trim();

    // Strip markdown code fences if present
    if (json.StartsWith("```"))
    {
        var firstNewline = json.IndexOf('\n');
        var lastFence = json.LastIndexOf("```");
        if (firstNewline > 0 && lastFence > firstNewline)
            json = json[(firstNewline + 1)..lastFence].Trim();
    }

    return System.Text.Json.JsonSerializer.Deserialize<List<BOMEntryDto>>(json,
        new System.Text.Json.JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        }) ?? [];
}

static void PrintResult(BomImportResult result)
{
    Console.WriteLine($"  Totali:    {result.TotalRows}");
    Console.WriteLine($"  Importati: {result.ImportedRows}");
    Console.WriteLine($"  Falliti:   {result.FailedRows}");

    foreach (var warning in result.Warnings)
        Console.WriteLine($"  [WARN] {warning}");

    foreach (var error in result.Errors)
        Console.Error.WriteLine($"  [ERROR] {error}");
}
