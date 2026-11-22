import openpyxl, datetime
import pandas as pd

print("Loading report.xlsx sheet FD...")
wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\report.xlsx', read_only=True)
ws = wb['FD']

data = []
for r in ws.iter_rows(min_row=2, max_col=8, values_only=True):
    if r[0] is not None:
        data.append({
            'date': r[0],
            'region': r[1],
            'id': r[2],
            'bc': r[3],
            'client_type': r[4],
            'total': r[5] or 0,
            'return': r[6] or 0,
            'am': r[7]
        })
wb.close()

df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

# Filter NTB and has AM
df = df[df['am'].notna() & (df['am'] != '')]
df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
df['return'] = pd.to_numeric(df['return'], errors='coerce').fillna(0)

df['iso_week'] = df['date'].dt.isocalendar().week
df['iso_year'] = df['date'].dt.isocalendar().year

w44_df = df[(df['iso_year'] == 2026) & (df['iso_week'] == 44)]
w45_df = df[(df['iso_year'] == 2026) & (df['iso_week'] == 45)]

# Group by AM for W44 and W45
am_w44 = w44_df.groupby('am').agg({'total': 'sum', 'return': 'sum'})
am_w44['rate_w44'] = am_w44['return'] / am_w44['total']

am_w45 = w45_df.groupby('am').agg({'total': 'sum', 'return': 'sum'})
am_w45['rate_w45'] = am_w45['return'] / am_w45['total']

all_ams = sorted(list(set(am_w44.index).union(set(am_w45.index))))
am_res = pd.DataFrame(index=all_ams)
am_res['w44_total'] = am_w44['total']
am_res['w44_return'] = am_w44['return']
am_res['rate_w44'] = am_w44['rate_w44']
am_res['w45_total'] = am_w45['total']
am_res['w45_return'] = am_w45['return']
am_res['rate_w45'] = am_w45['rate_w45']
am_res['diff'] = am_res['rate_w45'] - am_res['rate_w44']

print("\n=== AM FD SUMMARY (W44 vs W45) ===")
for am, r in am_res.iterrows():
    r44 = f"{r['rate_w44']*100:.2f}%" if pd.notna(r['rate_w44']) else "None"
    r45 = f"{r['rate_w45']*100:.2f}%" if pd.notna(r['rate_w45']) else "None"
    diff = f"{r['diff']*100:+.2f}%p" if pd.notna(r['diff']) else "None"
    print(f"- {am:12s} | W44: {r44:7s} (tot={r['w44_total']}, ret={r['w44_return']}) | W45: {r45:7s} (tot={r['w45_total']}, ret={r['w45_return']}) | Δ: {diff}")

# Also group by Bưu cục
bc_w44 = w44_df.groupby(['bc', 'am']).agg({'total': 'sum', 'return': 'sum'})
bc_w44['rate_w44'] = bc_w44['return'] / bc_w44['total']

bc_w45 = w45_df.groupby(['bc', 'am']).agg({'total': 'sum', 'return': 'sum'})
bc_w45['rate_w45'] = bc_w45['return'] / bc_w45['total']

all_bcs = list(set(bc_w44.index).union(set(bc_w45.index)))
bc_res = pd.DataFrame(index=pd.MultiIndex.from_tuples(all_bcs, names=['bc', 'am']))
bc_res['w44_total'] = bc_w44['total']
bc_res['w44_return'] = bc_w44['return']
bc_res['rate_w44'] = bc_w44['rate_w44']
bc_res['w45_total'] = bc_w45['total']
bc_res['w45_return'] = bc_w45['return']
bc_res['rate_w45'] = bc_w45['rate_w45']
bc_res['diff'] = bc_res['rate_w45'] - bc_res['rate_w44']

print("\n=== TOP 10 BUU CUC HIGHEST W45 FD ===")
top10_w45 = bc_res.sort_values(by='rate_w45', ascending=False).head(15)
for (bc, am), r in top10_w45.iterrows():
    r44 = f"{r['rate_w44']*100:.2f}%" if pd.notna(r['rate_w44']) else "None"
    r45 = f"{r['rate_w45']*100:.2f}%" if pd.notna(r['rate_w45']) else "None"
    diff = f"{r['diff']*100:+.2f}%p" if pd.notna(r['diff']) else "None"
    print(f"- {bc:30s} ({am:10s}) | Tot_W45: {r['w45_total']:5.0f} | Ret_W45: {r['w45_return']:3.0f} | W44: {r44:7s} | W45: {r45:7s} | Δ: {diff}")
