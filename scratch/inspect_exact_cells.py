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

print("NTBo C6:", repr(ws_ntbo.acell('C6').value))
print("NTBo J5:", repr(ws_ntbo.acell('J5').value))
print("raw B1484:", repr(ws_raw.acell('B1484').value))
print("raw C1484:", repr(ws_raw.acell('C1484').value))
print("raw D1484:", repr(ws_raw.acell('D1484').value))
print("raw E1484:", repr(ws_raw.acell('E1484').value))
print("raw J1484:", repr(ws_raw.acell('J1484').value))

# Also check date serial / type in Google Sheets:
# In Google Sheets, when you write '2026-11-03' via API as string vs USER_ENTERED (date)
print("NTBo J5 user entered value / formula:", ws_ntbo.acell('J5', value_render_option='UNFORMATTED_VALUE').value)
print("raw D1484 unformatted value:", ws_raw.acell('D1484', value_render_option='UNFORMATTED_VALUE').value)
