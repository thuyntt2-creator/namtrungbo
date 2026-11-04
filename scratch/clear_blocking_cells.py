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

print("A1 formula:", repr(ws_raw.acell('A1', value_render_option='FORMULA').value))
# CLEAR D1484 and D1506 immediately!
ws_raw.update_acell('D1484', '')
ws_raw.update_acell('D1506', '')
print("Cleared D1484 and D1506!")
