import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk')
ws_data = sh.worksheet('Data')

print("Total rows in Data:", ws_data.row_count)
col_d = ws_data.col_values(4)
print("Col D total entries:", len(col_d))
print("Sample entries in Col D:", col_d[:5], col_d[-5:])

