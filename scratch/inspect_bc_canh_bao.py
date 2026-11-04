import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

ws_bc = sh.worksheet('BC_canh_bao')
print("BC_canh_bao rows for NTB:")
for r in ws_bc.get_all_values()[4:25]:
    if len(r) > 4 and r[0] == 'NTB':
        print(f"  Tỉnh: {r[1]} | BC: {r[3]} | 7D: {r[4]} | Best: {r[5]} | N-1 ({ws_bc.cell(4,8).value}): {r[7]} | Vol N-1: {r[8]}")

