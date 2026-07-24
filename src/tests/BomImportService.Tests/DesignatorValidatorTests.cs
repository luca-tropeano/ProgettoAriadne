using BomImportService.Services;

namespace BomImportService.Tests;

public class DesignatorValidatorTests
{
    private readonly DesignatorValidator _validator = new();

    [Theory]
    [InlineData("C1", "C")]
    [InlineData("C5", "C")]
    [InlineData("C123", "C")]
    [InlineData("R10", "R")]
    [InlineData("R100", "R")]
    [InlineData("L1", "L")]
    [InlineData("D3", "D")]
    [InlineData("Q1", "Q")]
    [InlineData("U1", "U")]
    [InlineData("J1", "J")]
    [InlineData("P1", "P")]
    [InlineData("X1", "X")]
    [InlineData("Y1", "Y")]
    [InlineData("F1", "F")]
    [InlineData("T1", "T")]
    [InlineData("K1", "K")]
    [InlineData("M1", "M")]
    [InlineData("B1", "B")]
    [InlineData("Z1", "Z")]
    [InlineData("H1", "H")]
    public void GetDesignatorCode_SingleCharPrefix_ReturnsCorrectCode(string reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("C1,C5,C7,C8,C9", "C")]
    [InlineData("R1,R2,R3", "R")]
    [InlineData("U1,U2,U3,U4", "U")]
    public void GetDesignatorCode_MultipleDesignators_UsesFirstChar(string reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("SW1", "SW")]
    [InlineData("SW10", "SW")]
    public void GetDesignatorCode_Switch_ReturnsSW(string reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("ANT1", "ANT")]
    [InlineData("ANT3", "ANT")]
    public void GetDesignatorCode_Antenna_ReturnsANT(string reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("", "UNKNOWN")]
    [InlineData("  ", "UNKNOWN")]
    [InlineData(null, "UNKNOWN")]
    public void GetDesignatorCode_EmptyOrNull_ReturnsUnknown(string? reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference!);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("c1", "C")]
    [InlineData("r10", "R")]
    public void GetDesignatorCode_Lowercase_ConvertsToUpperCase(string reference, string expected)
    {
        var result = _validator.GetDesignatorCode(reference);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void GetDesignatorCode_UnknownPrefix_ReturnsUNKNOWN()
    {
        var result = _validator.GetDesignatorCode("99");
        Assert.Equal("UNKNOWN", result);
    }
}
