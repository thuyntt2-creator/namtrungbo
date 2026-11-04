import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws = sh.worksheet('NTBo')
print("Cell A2 text:", repr(ws.acell('A2').value))
print("Cell A2 formula:", repr(ws.acell('A2', value_render_option='FORMULA').value))
# also check A1:C3
for r in ws.get_values('A1:D3', value_render_option='FORMULA'):
    print(r)

