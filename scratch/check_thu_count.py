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

col_d = ws_raw.col_values(4)[1:]
has_thu = [v for v in col_d if ' - ' in v or 'Thứ' in v or 'Chủ Nhật' in v]
print(f"Total rows in raw Col D: {len(col_d)}")
print(f"Rows with ' - Thứ / Chủ Nhật': {len(has_thu)}")
print("Sample values in Col D:", col_d[:5], col_d[-5:])

