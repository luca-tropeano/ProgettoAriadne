using BomImportService.Interfaces;

namespace BomImportService.Services;

public class DesignatorValidator : IDesignatorValidator
{
    private static readonly Dictionary<char, string> PrefixMap = new()
    {
        { 'R', "R" }, { 'C', "C" }, { 'L', "L" }, { 'D', "D" },
        { 'Q', "Q" }, { 'U', "U" }, { 'J', "J" }, { 'P', "P" },
        { 'X', "X" }, { 'Y', "Y" }, { 'S', "SW" },
        { 'F', "F" }, { 'T', "T" }, { 'K', "K" }, { 'M', "M" },
        { 'B', "B" }, { 'Z', "Z" }, { 'A', "ANT" }, { 'H', "H" },
    };

    public string GetDesignatorCode(string reference)
    {
        if (string.IsNullOrWhiteSpace(reference))
            return "UNKNOWN";

        var trimmed = reference.Trim().ToUpperInvariant();
        var first = trimmed[0];

        if (PrefixMap.TryGetValue(first, out var code))
            return code;

        var prefix = trimmed;
        foreach (var kvp in PrefixMap.Where(k => k.Value.Length > 1)
                     .OrderByDescending(k => k.Value.Length))
        {
            if (prefix.StartsWith(kvp.Value))
                return kvp.Value;
        }

        return "UNKNOWN";
    }
}
