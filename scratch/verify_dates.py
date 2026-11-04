import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

ws_ntbo = sh.worksheet('NTBo')
ws_raw = sh.worksheet('raw')

# Check raw rows for Đức Trọng 1 on 2026-11-02
print("=== Checking Đức Trọng 1 in raw on 2026-11-02 ===")
raw_rows = ws_raw.get_all_values()
dt_rows_1102 = []
dt_rows_1103 = []
for r in raw_rows[1:]:
    if len(r) > 3 and '(LDO) Đức Trọng 1' in r[1]:
        if '2026-11-02' in r[3] or '02/11/2026' in r[3]:
            dt_rows_1102.append(r)
        if '2026-11-03' in r[3] or '03/11/2026' in r[3]:
            dt_rows_1103.append(r)

print(f"Found {len(dt_rows_1102)} rows on 2026-11-02:")
for r in dt_rows_1102:
    print("  ", r[:11])

print(f"Found {len(dt_rows_1103)} rows on 2026-11-03:")
for r in dt_rows_1103:
    print("  ", r[:11])

# Check if ANY row in raw has 2026-11-03 or 03/11/2026 or 3/11/2026
found_1103 = [r for r in raw_rows[1:] if len(r) > 3 and ('11-03' in r[3] or '03/11' in r[3] or '3/11' in r[3])]
print(f"\nTotal rows in raw with date 03/11: {len(found_1103)}")

