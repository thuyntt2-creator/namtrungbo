import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\BaoCao_Tuan_NTB_W45_2026.xlsx', data_only=True)
ws = wb['09_Rot LC']
for r in range(40, 65):
    row_vals = [ws.cell(r, c).value for c in range(1, 7)]
    if any(row_vals):
        print(f"Row {r}: {row_vals}")
wb.close()

