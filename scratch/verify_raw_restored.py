import sys, gspread
from google.oauth2.credentials import Credentials
import time

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_raw = sh.worksheet('raw')

time.sleep(2)
print("A1 value:", ws_raw.acell('A1').value)
print("A2 value:", ws_raw.acell('A2').value)
print("D2 value:", ws_raw.acell('D2').value)
print("Total rows:", len(ws_raw.col_values(1)))

ws_ntbo = sh.worksheet('NTBo')
print("\nNTBo row 6:")
h5 = ws_ntbo.row_values(5)
r6 = ws_ntbo.row_values(6)
for h, v in zip(h5[:12], r6[:12]):
    print(f"  {h}: {v}")

