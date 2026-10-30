import openpyxl

paths = [
    r'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx',
    r'c:\Users\lap4all\Desktop\New folder\Capacity_Planning_Test\[GHN]_Capacity Planning_Test_T10.2026\BAO_CAO_CAPACITY_11.11_FINAL.xlsx'
]

for p in paths:
    wb = openpyxl.load_workbook(p)
    ws = wb['canh_bao']
    for r in range(9, 177):
        formula_str = f"=VLOOKUP(B{r}, cap_hieu_chinh!$A$5:$H$16, 8, FALSE)"
        ws.cell(r, 5).value = formula_str
    wb.save(p)
    print('Linked canh_bao col E to cap_hieu_chinh for:', p)

