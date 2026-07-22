using System.Text;
using BomImportService.Interfaces;
using UglyToad.PdfPig;

namespace BomImportService.Services;

public class PdfExtractor : IPdfExtractor
{
    public string ExtractText(string pdfPath)
    {
        if (!File.Exists(pdfPath))
            throw new FileNotFoundException($"PDF not found: {pdfPath}");

        using var stream = File.OpenRead(pdfPath);
        return ExtractText(stream);
    }

    public string ExtractText(Stream pdfStream)
    {
        using var document = PdfDocument.Open(pdfStream);
        var sb = new StringBuilder();

        foreach (var page in document.GetPages())
        {
            var text = page.Text;

            if (!string.IsNullOrWhiteSpace(text))
            {
                sb.AppendLine($"--- Page {page.Number} ---");
                sb.AppendLine(text);
                sb.AppendLine();
            }
        }

        return sb.ToString();
    }
}
