import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_cb = sh.worksheet('BC_canh_bao')
cb_rows = ws_cb.get_all_values()

for r_idx in range(4):
    print(f"--- Row {r_idx} ---")
    for c_idx, val in enumerate(cb_rows[r_idx]):
        if val.strip():
            print(f"  Col {c_idx} ({chr(65+c_idx) if c_idx < 26 else 'A'+chr(65+c_idx-26)}): {val}")
