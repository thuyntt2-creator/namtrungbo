import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo')
ws_kt = sh.worksheet('Kiểm tra')
rows_kt = ws_kt.get_all_values()

for idx, r in enumerate(rows_kt[:15]):
    print(f"Row {idx}: {r[:18]}")
