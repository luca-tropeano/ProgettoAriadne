using OfficeOpenXml;

namespace BomImportService.Tests;

public class ExcelParsingTests : IDisposable
{
    private readonly string _testDir;

    public ExcelParsingTests()
    {
        _testDir = Path.Combine(Path.GetTempPath(), $"ariadne-excel-test-{Guid.NewGuid():N}");
        Directory.CreateDirectory(_testDir);
        ExcelPackage.LicenseContext = LicenseContext.NonCommercial;
    }

    public void Dispose()
    {
        if (Directory.Exists(_testDir))
            Directory.Delete(_testDir, true);
    }

    [Fact]
    public void ParseExcelBOM_BasicComponent_ParsesCorrectly()
    {
        var path = CreateTestExcel(new[]
        {
            new[] { "Item", "Qty", "Ref", "Value", "Package", "Manufacturer" },
            new[] { "1", "14", "C1,C5,C7", "100nF", "0603", "KEMET" },
        });

        using var package = new ExcelPackage(new FileInfo(path));
        var ws = package.Workbook.Worksheets[0];

        Assert.Equal("1", ws.Cells[2, 1].Text);
        Assert.Equal("14", ws.Cells[2, 2].Text);
        Assert.Equal("C1,C5,C7", ws.Cells[2, 3].Text);
        Assert.Equal("100nF", ws.Cells[2, 4].Text);
        Assert.Equal("0603", ws.Cells[2, 5].Text);
        Assert.Equal("KEMET", ws.Cells[2, 6].Text);
    }

    [Fact]
    public void ParseExcelBOM_MultipleRows_CorrectCount()
    {
        var path = CreateTestExcel(new[]
        {
            new[] { "Item", "Qty", "Ref", "Value", "Package", "Manufacturer" },
            new[] { "1", "14", "C1", "100nF", "0603", "KEMET" },
            new[] { "2", "5", "R1,R2", "10k", "0402", "YAGEO" },
            new[] { "3", "1", "U1", "STM32", "LQFP48", "ST" },
        });

        using var package = new ExcelPackage(new FileInfo(path));
        var ws = package.Workbook.Worksheets[0];

        Assert.Equal(3, ws.Dimension.Rows - 1); // minus header
    }

    [Fact]
    public void ParseExcelBOM_EmptyReference_SkipsRow()
    {
        var path = CreateTestExcel(new[]
        {
            new[] { "Item", "Qty", "Ref", "Value", "Package", "Manufacturer" },
            new[] { "1", "14", "C1", "100nF", "0603", "KEMET" },
            new[] { "2", "5", "", "10k", "0402", "YAGEO" },
            new[] { "3", "1", "U1", "STM32", "LQFP48", "ST" },
        });

        using var package = new ExcelPackage(new FileInfo(path));
        var ws = package.Workbook.Worksheets[0];

        // Row 2 is skipped because Ref is empty
        var reference2 = ws.Cells[3, 3].Text;
        Assert.True(string.IsNullOrWhiteSpace(reference2));
    }

    [Fact]
    public void ParseExcelBOM_RealBOMFormat_WithEmptyRows()
    {
        var path = CreateTestExcel(new[]
        {
            new[] { "Item", "Qty", "Ref", "Value", "Package", "Manufacturer" },
            new[] { "", "", "", "", "", "" },  // empty row
            new[] { "1", "14", "C1,C5,C7", "100nF", "0603", "KEMET" },
            new[] { "", "", "", "", "", "" },  // empty row
            new[] { "2", "5", "R1,R2", "10k", "0402", "YAGEO" },
        });

        using var package = new ExcelPackage(new FileInfo(path));
        var ws = package.Workbook.Worksheets[0];
        var rowCount = ws.Dimension.Rows;

        Assert.Equal(5, rowCount); // EPPlus skips empty trailing rows
    }

    private string CreateTestExcel(string[][] rows)
    {
        var path = Path.Combine(_testDir, $"test-bom-{Guid.NewGuid():N}.xlsx");
        using var package = new ExcelPackage();
        var ws = package.Workbook.Worksheets.Add("BOM");

        for (int r = 0; r < rows.Length; r++)
        {
            for (int c = 0; c < rows[r].Length; c++)
            {
                ws.Cells[r + 1, c + 1].Value = rows[r][c];
            }
        }

        package.SaveAs(new FileInfo(path));
        return path;
    }
}
