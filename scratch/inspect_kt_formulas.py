import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo')
ws_kt = sh.worksheet('Kiểm tra')

# Read formula in cells
formulas = ws_kt.get('I1:P10', value_render_option='FORMULA')
for idx, r in enumerate(formulas):
    print(f"Row {idx+1}: {r}")
