import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\BaoCao_Tuan_NTB_W45_2026.xlsx', data_only=True)
ws = wb['09_Rot LC']
print("Row 28:", [ws.cell(28, c).value for c in range(1, 6)])
print("Row 29:", [ws.cell(29, c).value for c in range(1, 6)])
wb.close()

