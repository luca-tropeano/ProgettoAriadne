using BomImportService.Interfaces;
using BomImportService.Models;
using BomImportService.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = Host.CreateDefaultBuilder(args)
    .ConfigureServices((context, services) =>
    {
        var config = context.Configuration.GetSection("Strapi").Get<StrapiConfig>()
            ?? throw new InvalidOperationException("Strapi config not found");

        services.AddSingleton<IStrapiClient>(_ =>
            new StrapiClient(config.BaseUrl, config.ApiToken));
        services.AddSingleton<IDesignatorValidator, DesignatorValidator>();
        services.AddSingleton<IEECClassifier, EECClassifier>();
        services.AddSingleton<BOMImportService>();
    })
    .Build();

var importService = host.Services.GetRequiredService<BOMImportService>();

// Esempio: import da file Excel
if (args.Length > 0)
{
    var filePath = args[0];
    await using var stream = File.OpenRead(filePath);
    var result = await importService.ImportBomAsync(stream, deviceId: 1, userId: "cli");

    Console.WriteLine($"Importati: {result.ImportedRows}, Falliti: {result.FailedRows}");
    foreach (var error in result.Errors)
        Console.Error.WriteLine(error);
}
else
{
    Console.WriteLine("Usage: BomImportService <path-to-excel.xlsx>");
}
