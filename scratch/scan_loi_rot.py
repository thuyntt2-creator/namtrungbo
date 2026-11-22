import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\report.xlsx', read_only=True)
ws = wb['data rớt LC']
print("Scanning report.xlsx data rớt LC for Lang Biang or Loi...")
found = []
for r in range(2, 500):
    bc = ws.cell(r, 2).value
    if bc and ('lang biang' in str(bc).lower() or 'loi' in str(bc).lower() or 'lợi' in str(bc).lower()):
        found.append([ws.cell(r, c).value for c in range(1, 7)])
print(f"Found {len(found)} rows:")
for row in found[:10]:
    print(row)
wb.close()

