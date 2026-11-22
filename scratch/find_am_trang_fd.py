import openpyxl, datetime
import pandas as pd

wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\report.xlsx', read_only=True)
ws = wb['FD']

lv_rows = []
for r in ws.iter_rows(min_row=2, max_col=8, values_only=True):
    if r[0] is not None:
        bc_str = str(r[3]).lower() if r[3] else ''
        am_str = str(r[7]).lower() if r[7] else ''
        if 'lâm viên' in bc_str or 'lam vien' in bc_str or 'trang' in am_str:
            lv_rows.append({
                'date': r[0],
                'bc': r[3],
                'client_type': r[4],
                'total': r[5] or 0,
                'return': r[6] or 0,
                'am': r[7]
            })
wb.close()

df = pd.DataFrame(lv_rows)
print(f"Total matching rows: {len(df)}")
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['iso_week'] = df['date'].dt.isocalendar().week
    print("Unique BCs:", df['bc'].unique())
    print("Unique AMs:", df['am'].unique())
    print("Group by week & bc:")
    print(df.groupby(['iso_week', 'bc', 'am']).agg({'total': 'sum', 'return': 'sum'}))
