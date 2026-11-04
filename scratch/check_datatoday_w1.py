import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_dt = sh.worksheet('Datatoday')

print("Datatoday cell W1:", repr(ws_dt.acell('W1').value))
print("Datatoday cell W1 formula:", repr(ws_dt.acell('W1', value_render_option='FORMULA').value))
# Check what error is on A1
print("Datatoday cell A1:", repr(ws_dt.acell('A1').value))

