import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh_cb = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_cb = sh_cb.worksheet('BC_canh_bao')
rows_cb = ws_cb.get_all_values()

headers = rows_cb[3]
for r in rows_cb[5:]:
    if len(r) > 3 and ('Trường Xuân' in r[3] or 'Quảng Khê' in r[3]):
        print(f"\n=== {r[3]} ===")
        for idx, val in enumerate(r):
            h = headers[idx] if idx < len(headers) else ""
            if val.strip():
                print(f"Col {idx:2d} ({chr(65+idx) if idx < 26 else 'A'+chr(65+idx-26)}): [{h:15s}] = {val}")

