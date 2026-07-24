using System.Diagnostics;
using System.Net.Http.Json;
using System.Text.Json;
using OfficeOpenXml;

ExcelPackage.LicenseContext = LicenseContext.NonCommercial;

var baseUrl = "http://localhost:1337";
var outputDir = @"C:\Users\lucat\Desktop\se26-p07\exports";
Directory.CreateDirectory(outputDir);
var outputPath = Path.Combine(outputDir, $"StrapiExport_{DateTime.Now:yyyyMMdd_HHmmss}.xlsx");

Console.WriteLine("Fetching data from Strapi...");

// ─── EEC CATEGORIES ───
Console.Write("  EEC Categories...");
var eecData = await FetchAll(baseUrl, "api/eec-category", 50);
Console.WriteLine($" {eecData.Count}");

// ─── REFERENCE DESIGNATORS ───
Console.Write("  Reference Designators...");
var rdData = await FetchAll(baseUrl, "api/reference-designator", 50);
Console.WriteLine($" {rdData.Count}");

// ─── BOM ENTRIES ───
Console.Write("  BOM Entries...");
var bomData = await FetchAll(baseUrl, "api/bom-entry", 100);
Console.WriteLine($" {bomData.Count}");

// ─── DEVICES ───
Console.Write("  Devices...");
var devData = await FetchAll(baseUrl, "api/device", 50);
Console.WriteLine($" {devData.Count}");

// ─── AUDIT LOGS ───
Console.Write("  Audit Logs...");
var logData = await FetchAll(baseUrl, "api/audit-log", 50);
Console.WriteLine($" {logData.Count}");

Console.WriteLine("Generating Excel...");

using var pkg = new ExcelPackage();

// ─── SUMMARY SHEET ───
var wsSum = pkg.Workbook.Worksheets.Add("Summary");
wsSum.Cells[1, 1].Value = "Strapi Database Export";
wsSum.Cells[1, 1].Style.Font.Size = 16;
wsSum.Cells[1, 1].Style.Font.Bold = true;
wsSum.Cells[3, 1].Value = "Export Date";
wsSum.Cells[3, 2].Value = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
SetBold(wsSum, 5, 1, 5, 2);
wsSum.Cells[5, 1].Value = "Table";
wsSum.Cells[5, 2].Value = "Records";
string[] tables = { "EEC Categories", "Reference Designators", "BOM Entries", "Devices", "Audit Logs" };
int[] counts = { eecData.Count, rdData.Count, bomData.Count, devData.Count, logData.Count };
for (int i = 0; i < tables.Length; i++)
{
    wsSum.Cells[6 + i, 1].Value = tables[i];
    wsSum.Cells[6 + i, 2].Value = counts[i];
}
SetBold(wsSum, 10, 1, 10, 2);
wsSum.Cells[10, 1].Value = "TOTAL";
wsSum.Cells[10, 2].Value = bomData.Count + eecData.Count + rdData.Count + devData.Count + logData.Count;

wsSum.Cells[12, 1].Value = "BOM by Designator";
wsSum.Cells[12, 1].Style.Font.Bold = true;
SetBold(wsSum, 13, 1, 13, 3);
wsSum.Cells[13, 1].Value = "Designator";
wsSum.Cells[13, 2].Value = "Entries";
wsSum.Cells[13, 3].Value = "Total Qty";

var bomGroups = bomData
    .GroupBy(b => b.TryGetProperty("designatorCode", out var dc) ? dc.GetString() ?? "?" : "?")
    .OrderBy(g => g.Key)
    .ToList();
int row = 14;
foreach (var g in bomGroups)
{
    wsSum.Cells[row, 1].Value = g.Key;
    wsSum.Cells[row, 2].Value = g.Count();
    wsSum.Cells[row, 3].Value = g.Sum(b => b.GetProperty("quantity").GetInt32());
    row++;
}
wsSum.Cells[row, 1].Value = "TOTAL";
wsSum.Cells[row, 2].Value = bomData.Count;
wsSum.Cells[row, 3].Value = bomData.Sum(b => b.GetProperty("quantity").GetInt32());
SetBold(wsSum, row, 1, row, 3);
wsSum.Cells.AutoFitColumns();

// ─── EEC CATEGORIES SHEET ───
var wsEec = pkg.Workbook.Worksheets.Add("EEC Categories");
string[] eecHeaders = { "ID", "DocumentId", "CategoryId", "Name", "Description", "Subcategories" };
WriteHeaders(wsEec, eecHeaders);
for (int i = 0; i < eecData.Count; i++)
{
    var e = eecData[i];
    wsEec.Cells[i + 2, 1].Value = GetInt(e, "id");
    wsEec.Cells[i + 2, 2].Value = GetStr(e, "documentId");
    wsEec.Cells[i + 2, 3].Value = GetInt(e, "categoryId");
    wsEec.Cells[i + 2, 4].Value = GetStr(e, "name");
    wsEec.Cells[i + 2, 5].Value = GetStr(e, "description");
    if (e.TryGetProperty("subcategories", out var subs))
    {
        var subList = new List<string>();
        foreach (var s in subs.EnumerateArray())
            subList.Add(s.GetString() ?? "");
        wsEec.Cells[i + 2, 6].Value = string.Join(", ", subList);
    }
}
wsEec.Cells.AutoFitColumns();

// ─── REFERENCE DESIGNATORS SHEET ───
var wsRd = pkg.Workbook.Worksheets.Add("Reference Designators");
string[] rdHeaders = { "ID", "DocumentId", "Code", "Name", "Description", "EEC Category", "EEC ID" };
WriteHeaders(wsRd, rdHeaders);
for (int i = 0; i < rdData.Count; i++)
{
    var r = rdData[i];
    wsRd.Cells[i + 2, 1].Value = GetInt(r, "id");
    wsRd.Cells[i + 2, 2].Value = GetStr(r, "documentId");
    wsRd.Cells[i + 2, 3].Value = GetStr(r, "designatorCode");
    wsRd.Cells[i + 2, 4].Value = GetStr(r, "name");
    wsRd.Cells[i + 2, 5].Value = GetStr(r, "description");
    if (r.TryGetProperty("eecCategory", out var cat) && cat.ValueKind == JsonValueKind.Object)
    {
        wsRd.Cells[i + 2, 6].Value = GetStr(cat, "name");
        wsRd.Cells[i + 2, 7].Value = GetInt(cat, "id");
    }
}
wsRd.Cells.AutoFitColumns();

// ─── BOM ENTRIES SHEET ───
var wsBom = pkg.Workbook.Worksheets.Add("BOM Entries");
string[] bomHeaders = {
    "ID", "DocId", "Item #", "Qty", "Reference Designators",
    "Part Value", "Manufacturer", "Mfr Order Code",
    "Supplier1", "Supplier1 Code", "Supplier2", "Supplier2 Code",
    "Supplier3", "Supplier3 Code", "Designator", "Mounting", "Notes"
};
WriteHeaders(wsBom, bomHeaders);
for (int i = 0; i < bomData.Count; i++)
{
    var b = bomData[i];
    wsBom.Cells[i + 2, 1].Value = GetInt(b, "id");
    wsBom.Cells[i + 2, 2].Value = GetStr(b, "documentId");
    wsBom.Cells[i + 2, 3].Value = GetInt(b, "itemNumber");
    wsBom.Cells[i + 2, 4].Value = GetInt(b, "quantity");
    wsBom.Cells[i + 2, 5].Value = GetStr(b, "referenceDesignator");
    wsBom.Cells[i + 2, 6].Value = GetStr(b, "partValue");
    wsBom.Cells[i + 2, 7].Value = GetStr(b, "manufacturer");
    wsBom.Cells[i + 2, 8].Value = GetStr(b, "manufacturerOrderCode");
    wsBom.Cells[i + 2, 9].Value = GetStr(b, "supplier1");
    wsBom.Cells[i + 2, 10].Value = GetStr(b, "supplier1OrderCode");
    wsBom.Cells[i + 2, 11].Value = GetStr(b, "supplier2");
    wsBom.Cells[i + 2, 12].Value = GetStr(b, "supplier2OrderCode");
    wsBom.Cells[i + 2, 13].Value = GetStr(b, "supplier3");
    wsBom.Cells[i + 2, 14].Value = GetStr(b, "supplier3OrderCode");
    wsBom.Cells[i + 2, 15].Value = GetStr(b, "designatorCode");
    wsBom.Cells[i + 2, 16].Value = GetStr(b, "mountingType");
    wsBom.Cells[i + 2, 17].Value = GetStr(b, "notes");
}
wsBom.Cells.AutoFitColumns();
wsBom.Cells[$"A1:{char.ConvertFromUtf32(64 + bomHeaders.Length)}{bomData.Count + 1}"].AutoFilter = true;

// ─── DEVICES SHEET ───
var wsDev = pkg.Workbook.Worksheets.Add("Devices");
string[] devHeaders = { "ID", "DocumentId", "Brand", "Model", "Manufacturer", "Year", "Notes" };
WriteHeaders(wsDev, devHeaders);
for (int i = 0; i < devData.Count; i++)
{
    var d = devData[i];
    wsDev.Cells[i + 2, 1].Value = GetInt(d, "id");
    wsDev.Cells[i + 2, 2].Value = GetStr(d, "documentId");
    wsDev.Cells[i + 2, 3].Value = GetStr(d, "brand");
    wsDev.Cells[i + 2, 4].Value = GetStr(d, "modelName");
    wsDev.Cells[i + 2, 5].Value = GetStr(d, "manufacturer");
    wsDev.Cells[i + 2, 6].Value = GetInt(d, "yearOfProduction");
    wsDev.Cells[i + 2, 7].Value = GetStr(d, "notes");
}
wsDev.Cells.AutoFitColumns();

// ─── AUDIT LOGS SHEET ───
var wsLog = pkg.Workbook.Worksheets.Add("Audit Logs");
string[] logHeaders = { "ID", "DocumentId", "Timestamp", "UserId", "Action", "Details" };
WriteHeaders(wsLog, logHeaders);
for (int i = 0; i < logData.Count; i++)
{
    var l = logData[i];
    wsLog.Cells[i + 2, 1].Value = GetInt(l, "id");
    wsLog.Cells[i + 2, 2].Value = GetStr(l, "documentId");
    wsLog.Cells[i + 2, 3].Value = GetStr(l, "timestamp");
    wsLog.Cells[i + 2, 4].Value = GetStr(l, "userId");
    wsLog.Cells[i + 2, 5].Value = GetStr(l, "action");
    wsLog.Cells[i + 2, 6].Value = GetStr(l, "details");
}
wsLog.Cells.AutoFitColumns();

// ─── SAVE ───
await pkg.SaveAsAsync(new FileInfo(outputPath));
Console.WriteLine($"\nExported: {outputPath}");
Console.WriteLine($"Sheets: {pkg.Workbook.Worksheets.Count}");
Process.Start(new ProcessStartInfo(outputPath) { UseShellExecute = true });

// ─── HELPERS ───
static async Task<List<JsonElement>> FetchAll(string baseUrl, string endpoint, int pageSize)
{
    using var http = new HttpClient { BaseAddress = new Uri(baseUrl) };
    var all = new List<JsonElement>();
    int page = 1;
    while (true)
    {
        var url = $"{endpoint}?pagination[page]={page}&pagination[pageSize]={pageSize}";
        var resp = await http.GetAsync(url);
        if (!resp.IsSuccessStatusCode) break;
        var json = await resp.Content.ReadFromJsonAsync<JsonElement>();
        if (!json.TryGetProperty("data", out var data) || data.GetArrayLength() == 0) break;
        foreach (var item in data.EnumerateArray())
            all.Add(item);
        if (data.GetArrayLength() < pageSize) break;
        page++;
    }
    return all;
}

static void WriteHeaders(ExcelWorksheet ws, string[] headers)
{
    for (int c = 0; c < headers.Length; c++)
    {
        ws.Cells[1, c + 1].Value = headers[c];
        ws.Cells[1, c + 1].Style.Font.Bold = true;
        ws.Cells[1, c + 1].Style.Fill.PatternType = OfficeOpenXml.Style.ExcelFillStyle.Solid;
        ws.Cells[1, c + 1].Style.Fill.BackgroundColor.SetColor(System.Drawing.Color.FromArgb(31, 119, 180));
        ws.Cells[1, c + 1].Style.Font.Color.SetColor(System.Drawing.Color.White);
    }
}

static void SetBold(ExcelWorksheet ws, int row, int colStart, int rowEnd, int colEnd)
{
    for (int r = row; r <= rowEnd; r++)
        for (int c = colStart; c <= colEnd; c++)
            ws.Cells[r, c].Style.Font.Bold = true;
}

static string GetStr(JsonElement el, string prop)
    => el.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";

static int GetInt(JsonElement el, string prop)
    => el.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetInt32() : 0;
