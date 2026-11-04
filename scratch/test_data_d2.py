import sys, gspread
from google.oauth2.credentials import Credentials
import time

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh_src = gc.open_by_key('1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk')
ws_data = sh_src.worksheet('Data')

old_val = ws_data.acell('D2').value
print("Old D2 in Data:", old_val)

ws_data.update_acell('D2', '2026-10-08')
time.sleep(2)

new_val = ws_data.acell('D2').value
unformatted = ws_data.acell('D2', value_render_option='UNFORMATTED_VALUE').value
print("New D2 in Data:", new_val)
print("Unformatted D2 in Data:", unformatted)

# Revert back to old_val
ws_data.update_acell('D2', old_val)

