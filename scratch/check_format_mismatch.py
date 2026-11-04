import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

ws_ntbo = sh.worksheet('NTBo')
ws_raw = sh.worksheet('raw')

print("Sample raw row 2:")
print(ws_raw.row_values(2))
print("Col D value:", repr(ws_raw.cell(2, 4).value))

print("\nNTBo J5:")
print("Value:", repr(ws_ntbo.cell(5, 10).value))
print("Formula:", repr(ws_ntbo.acell('J5', value_render_option='FORMULA').value))
