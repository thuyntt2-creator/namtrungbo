import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

# Check row 6 across all columns D to N
ws_ntbo = sh.worksheet('NTBo')
r6 = ws_ntbo.row_values(6)
h5 = ws_ntbo.row_values(5)
for h, v in zip(h5, r6):
    print(f"{h}: {v}")

# Check tab raw row count and last 5 rows
ws_raw = sh.worksheet('raw')
print(f"\nTab raw rows: {ws_raw.row_count}")
col_d = ws_raw.col_values(4)
print(f"Tab raw Col D count: {len(col_d)}")
print("Tab raw unique dates (last 10):", sorted(list(set(col_d[1:])))[-10:])
