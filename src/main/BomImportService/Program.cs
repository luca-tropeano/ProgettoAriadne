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

        services.AddSingleton<IStrapiClient>(_ =>
            new StrapiClient(strapiConfig.BaseUrl, strapiConfig.ApiToken));
        services.AddSingleton<IDesignatorValidator, DesignatorValidator>();
        services.AddSingleton<IEECClassifier, EECClassifier>();
        services.AddSingleton<IPdfExtractor, PdfExtractor>();
        services.AddSingleton<BOMImportService>();
    })
    .Build();

var importService = host.Services.GetRequiredService<BOMImportService>();
var pdfExtractor = host.Services.GetRequiredService<IPdfExtractor>();

var flags = ParseFlags(args);

if (flags.TryGetValue("--file", out var filePath) == false && args.Length > 0 && !args[0].StartsWith("--"))
{
    filePath = args[0];
}

if (string.IsNullOrEmpty(filePath))
{
    Console.WriteLine("Usage: BomImportService <file> [--brand X] [--model X] [--manufacturer X] [--year N]");
    Console.WriteLine("  .xlsx  — import diretto da Excel");
    Console.WriteLine("  .pdf   — estrazione via AI → Strapi");
    Console.WriteLine();
    Console.WriteLine("Options:");
    Console.WriteLine("  --brand         Device brand (e.g. STMicroelectronics)");
    Console.WriteLine("  --model         Device model (e.g. STEVAL-SPIN3204)");
    Console.WriteLine("  --manufacturer  Device manufacturer");
    Console.WriteLine("  --year          Year of production");
    return;
}

var ext = Path.GetExtension(filePath).ToLowerInvariant();

DeviceDto? deviceInfo = null;
if (flags.ContainsKey("--brand") || flags.ContainsKey("--model"))
{
    deviceInfo = new DeviceDto
    {
        Brand = flags.GetValueOrDefault("--brand", ""),
        ModelName = flags.GetValueOrDefault("--model", ""),
        Manufacturer = flags.GetValueOrDefault("--manufacturer",
            flags.GetValueOrDefault("--brand", "")),
        YearOfProduction = int.TryParse(flags.GetValueOrDefault("--year", ""), out var yr) ? yr : DateTime.Now.Year
    };
}

string? deviceDocId = null;
if (deviceInfo != null && !string.IsNullOrEmpty(deviceInfo.ModelName))
{
    deviceDocId = await importService.FindOrCreateDeviceAsync(deviceInfo);
}

switch (ext)
{
    case ".xlsx":
    case ".xls":
        Console.WriteLine($"Import Excel: {filePath}");
        await using (var stream = File.OpenRead(filePath))
        {
            var excelResult = await importService.ImportBomAsync(stream, deviceDocId, "cli");
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

        // AI extraction non più integrata direttamente qui — usa la pipeline Python ariadne-py

        Console.WriteLine($"Extracted {entries.Count} components from PDF.");
        Console.WriteLine("Importing to Strapi...");

        var pdfResult = await importService.ImportBomFromEntriesAsync(entries, deviceDocId, "cli");
        PrintResult(pdfResult);
        break;

    default:
        Console.Error.WriteLine($"Unsupported file format: {ext}");
        Console.WriteLine("Supported formats: .xlsx, .xls, .pdf");
        break;
}

static Dictionary<string, string> ParseFlags(string[] args)
{
    var flags = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    for (int i = 0; i < args.Length; i++)
    {
        if (args[i].StartsWith("--") && i + 1 < args.Length && !args[i + 1].StartsWith("--"))
        {
            flags[args[i].ToLowerInvariant()] = args[i + 1];
            i++;
        }
        else if (!args[i].StartsWith("--"))
        {
            flags.TryAdd("--file", args[i]);
        }
    }
    return flags;
}

static List<BOMEntryDto> ParseAiResponse(string response)
{
    var json = response.Trim();

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
