import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\BaoCao_Tuan_NTB_W45_2026.xlsx', data_only=True)
ws = wb['09_Rot LC']
print("=== ALL AMs (Rows 10-31) ===")
for r in range(10, 32):
    vals = [ws.cell(r, c).value for c in range(1, 7)]
    if any(vals):
        print(f"Row {r}: {vals}")

print("\n=== ALL PROVINCES (Rows 32-40) ===")
for r in range(32, 41):
    vals = [ws.cell(r, c).value for c in range(1, 7)]
    if any(vals):
        print(f"Row {r}: {vals}")
wb.close()

