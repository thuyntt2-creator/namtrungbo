import sys, json
import gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

# 1. Inspect tab NTBo row 5 headers
ws_ntbo = sh.worksheet('NTBo')
headers = ws_ntbo.row_values(5)
print("=== HEADERS ROW 5 IN NTBo ===")
for col_idx, h in enumerate(headers):
    col_letter = chr(65 + col_idx) if col_idx < 26 else f"A{chr(65 + col_idx - 26)}"
    print(f"Col {col_letter} ({col_idx+1}): {repr(h)}")

# 2. Inspect tab raw
ws_raw = sh.worksheet('raw')
print(f"\n=== TAB RAW (rows={ws_raw.row_count}, cols={ws_raw.col_count}) ===")
raw_headers = ws_raw.row_values(1)
print(f"Raw headers: {raw_headers}")

# Check distinct dates in Col D of raw
# Col D is index 3
col_d_values = ws_raw.col_values(4)
print(f"Total values in raw Col D: {len(col_d_values)}")
dates = set(col_d_values[1:])
print("Distinct dates in raw Col D:", sorted(list(dates)))

# Check the last 15 rows of raw
raw_last = ws_raw.get_values(f'A{max(1, len(col_d_values)-10)}:J{len(col_d_values)}')
print("\nLast 10 rows of raw:")
for r in raw_last:
    print(r)

