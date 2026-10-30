import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_cb = sh.worksheet('BC_canh_bao')
cb_rows = ws_cb.get_all_values()

print("Header row 3 (0-indexed 3):")
for i, h in enumerate(cb_rows[3]):
    print(f"Col {i} ({chr(65+i) if i < 26 else 'A'+chr(65+i-26)}): {h}")

print("\nSample Data row 5 (0-indexed 5):")
for i, val in enumerate(cb_rows[5]):
    h = cb_rows[3][i] if i < len(cb_rows[3]) else ""
    print(f"Col {i} [{h}]: {val}")
