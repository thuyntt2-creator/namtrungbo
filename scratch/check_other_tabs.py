import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

for name in ['raw_buu_cuc_canh_bao', 'raw_buu_cuc_canh_bao_2', 'NTB', 'BC_canh_bao']:
    try:
        ws = sh.worksheet(name)
        dates = set(ws.col_values(4)[1:50])
        print(f"Tab '{name}' sample col D:", list(dates)[:5])
    except Exception as e:
        print(f"Tab '{name}' err:", e)

