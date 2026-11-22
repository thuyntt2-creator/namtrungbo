import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\BaoCao_Tuan_NTB_W45_2026.xlsx', data_only=True)
ws = wb['09_Rot LC']
print("=== 09_Rot LC in BaoCao_Tuan_NTB_W45_2026.xlsx ===")
for r in range(1, 40):
    row_vals = [ws.cell(r, c).value for c in range(1, 15)]
    if any(row_vals):
        print(f"Row {r}: {row_vals}")
wb.close()

