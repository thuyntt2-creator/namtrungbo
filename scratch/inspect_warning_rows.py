import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_cb = sh.worksheet('BC_canh_bao')
cb_rows = ws_cb.get_all_values()

for r in cb_rows[5:]:
    if len(r) > 3 and r[3].strip() and ('Cảnh báo' in r[18] or '<' in r[18]):
        bc = r[3].strip()
        gtc_7d = r[4]
        gtc_best = r[5]
        m70 = r[6]
        c14 = r[14]
        vol_can_giao = r[15]
        print(f"BC: {bc:28} | %GTC 7D (E): {gtc_7d:7} | GTC Best (F): {gtc_best:7} | 70% Best (G): {m70:7} | Col O (14): {c14:5} | Vol cần giao (P/15): {vol_can_giao:5} | Warning: {r[18]}")

