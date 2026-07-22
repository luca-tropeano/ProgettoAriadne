namespace BomImportService.Interfaces;

public interface IPdfExtractor
{
    string ExtractText(string pdfPath);
    string ExtractText(Stream pdfStream);
}
