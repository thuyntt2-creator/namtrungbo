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
ws_ntbo = sh.worksheet('NTBo')

ws_raw.update_acell('D1484', '2026-11-03')
ws_raw.update_acell('D1506', '2026-11-03')

import time
time.sleep(2)

val_j6 = ws_ntbo.acell('J6').value
print("Value of NTBo!J6 after changing D1484 & D1506 to '2026-11-03':", val_j6)

