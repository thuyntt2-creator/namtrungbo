import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
try:
    sh_src = gc.open_by_key('1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk')
    print("Opened source sheet:", sh_src.title)
    ws_data = sh_src.worksheet('Data')
    print("Data row 1:", ws_data.row_values(1)[:6])
    print("Data row 2:", ws_data.row_values(2)[:6])
    print("Data row 2 Col D unformatted:", ws_data.acell('D2', value_render_option='UNFORMATTED_VALUE').value)
    print("Data row 2 Col D formula:", ws_data.acell('D2', value_render_option='FORMULA').value)
except Exception as e:
    print("Error opening source sheet:", e)

