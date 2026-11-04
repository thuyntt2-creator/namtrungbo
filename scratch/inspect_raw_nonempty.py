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

all_vals = ws_raw.get_all_values()
print(f"Total rows retrieved from raw: {len(all_vals)}")
non_empty = [i for i, r in enumerate(all_vals) if any(c != '' for c in r)]
print(f"Non-empty rows count: {len(non_empty)}")
if non_empty:
    print(f"First non-empty row index: {non_empty[0]+1}")
    print(f"Last non-empty row index: {non_empty[-1]+1}")
    for idx in non_empty[:5]:
        print(f"Row {idx+1}: {all_vals[idx][:6]}")
    for idx in non_empty[-5:]:
        print(f"Row {idx+1}: {all_vals[idx][:6]}")
