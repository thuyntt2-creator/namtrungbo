import openpyxl, datetime

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\report.xlsx', read_only=True)
ws = wb['data rớt LC']

# Find min and max date in ltc_date (column 3)
min_date = None
max_date = None
row_count = 0
for r in range(2, 20000):
    val = ws.cell(r, 3).value
    if val is None:
        break
    row_count += 1
    if isinstance(val, datetime.datetime):
        if min_date is None or val < min_date:
            min_date = val
        if max_date is None or val > max_date:
            max_date = val

print(f"Total rows in data rớt LC: {row_count}")
print(f"Date range: {min_date} to {max_date}")
wb.close()

