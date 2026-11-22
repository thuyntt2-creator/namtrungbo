import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\BaoCao_Tuan_NTB_W45_2026.xlsx', data_only=True)
ws = wb['12_FD']
print('Rows in 12_FD:')
for i in range(1, ws.max_row + 1):
    vals = [ws.cell(i, j).value for j in range(1, 10)]
    if any(vals):
        print(f'{i}: {vals}')

