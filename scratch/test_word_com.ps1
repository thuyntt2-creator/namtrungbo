try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    Write-Host "Word COM is available: $($word.Version)"
    
    $sourceAsd = "C:\Users\lap4all\AppData\Local\Microsoft\Office\UnsavedFiles\BAI TOAN 1((Unsaved-312870380708660752)).asd"
    $outDocx = "C:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAI_TOAN_1_DON_TAO_VA_DON_VE_HOAN_CHINH.docx"
    
    # In Word, Documents.Open can open ASD files natively
    $doc = $word.Documents.Open($sourceAsd)
    Write-Host "Opened successfully! Paragraphs count: $($doc.Paragraphs.Count)"
    
    # Save as DOCX (wdFormatXMLDocument = 12)
    $doc.SaveAs2($outDocx, 12)
    $doc.Close()
    $word.Quit()
    
    Write-Host "SUCCESSFULLY SAVED TO: $outDocx"
}
catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($word) { $word.Quit() }
}

b