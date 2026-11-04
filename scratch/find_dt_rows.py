import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_raw = sh.worksheet('raw')

raw_vals = ws_raw.get_all_values()
for idx, r in enumerate(raw_vals):
    if '(LDO) Đức Trọng 1' in r[1] and '2026-11-03' in r[3]:
        print(f"Row {idx+1}: {r[1]} | {r[2]} | {r[3]}")

