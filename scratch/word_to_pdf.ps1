$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = 'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\Bao_Cao_Nang_Luc_11.11_Vong1.docx'
$pdfPath = 'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\Bao_Cao_Nang_Luc_11.11_Vong1.pdf'
try {
    $doc = $word.Documents.Open($docPath)
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    $pageCount = $doc.ComputeStatistics(2)
    $doc.Close()
    Write-Host "Successfully converted to PDF. Page count: $pageCount"
} catch {
    Write-Host "Error: $_"
}
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null

