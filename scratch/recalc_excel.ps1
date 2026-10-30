$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$paths = @(
    'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx',
    'c:\Users\lap4all\Desktop\New folder\Capacity_Planning_Test\[GHN]_Capacity Planning_Test_T10.2026\BAO_CAO_CAPACITY_11.11_FINAL.xlsx'
)
foreach ($p in $paths) {
    try {
        $wb = $excel.Workbooks.Open($p)
        $excel.CalculateFull()
        $wb.Save()
        $wb.Close()
        Write-Host "Recalculated and saved: $p"
    } catch {
        Write-Host "Error with $p : $_"
    }
}
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

