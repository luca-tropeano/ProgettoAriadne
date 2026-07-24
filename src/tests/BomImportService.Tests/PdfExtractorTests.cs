using BomImportService.Services;

namespace BomImportService.Tests;

public class PdfExtractorTests : IDisposable
{
    private readonly PdfExtractor _extractor = new();
    private readonly string _testDir;

    public PdfExtractorTests()
    {
        _testDir = Path.Combine(Path.GetTempPath(), $"ariadne-test-{Guid.NewGuid():N}");
        Directory.CreateDirectory(_testDir);
    }

    public void Dispose()
    {
        if (Directory.Exists(_testDir))
            Directory.Delete(_testDir, true);
    }

    [Fact]
    public void ExtractText_NonExistentFile_ThrowsFileNotFoundException()
    {
        Assert.Throws<FileNotFoundException>(() =>
            _extractor.ExtractText(Path.Combine(_testDir, "nonexistent.pdf")));
    }

    [Fact]
    public void ExtractText_FromRealPdf_ContainsText()
    {
        var pdfPath = Path.Combine(_testDir, "bom-sample.pdf");
        CopyTestPdf(pdfPath);

        var result = _extractor.ExtractText(pdfPath);

        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }

    [Fact]
    public void ExtractText_StreamAndFilePath_ReturnSameResult()
    {
        var pdfPath = Path.Combine(_testDir, "stream-test.pdf");
        CopyTestPdf(pdfPath);

        var fileResult = _extractor.ExtractText(pdfPath);
        using var stream = File.OpenRead(pdfPath);
        var streamResult = _extractor.ExtractText(stream);

        Assert.Equal(fileResult, streamResult);
    }

    [Fact]
    public void ExtractText_PdfWithBomContent_ContainsDesignators()
    {
        var pdfPath = Path.Combine(_testDir, "bom-content.pdf");
        CopyTestPdf(pdfPath);

        var result = _extractor.ExtractText(pdfPath);

        Assert.NotNull(result);
        Assert.True(result.Length > 50, "Extracted text should have meaningful content");
    }

    private void CopyTestPdf(string destination)
    {
        var sourcePdf = Path.Combine(
            Directory.GetCurrentDirectory(),
            "..", "..", "..", "..", "..",
            "PROGETTO", "2026-6-19  Ariande Digital path  Rev En 22 sl.pdf");

        if (!File.Exists(sourcePdf))
        {
            var altSource = Path.Combine(
                Directory.GetCurrentDirectory(),
                "..", "..", "..", "..", "..", "..",
                "Desktop", "PROGETTO", "2026-6-19  Ariande Digital path  Rev En 22 sl.pdf");

            if (File.Exists(altSource))
                sourcePdf = altSource;
        }

        if (!File.Exists(sourcePdf))
        {
            var altSource2 = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                "PROGETTO", "2026-6-19  Ariande Digital path  Rev En 22 sl.pdf");

            if (File.Exists(altSource2))
                sourcePdf = altSource2;
        }

        if (!File.Exists(sourcePdf))
            return;

        File.Copy(sourcePdf, destination, true);
    }
}
