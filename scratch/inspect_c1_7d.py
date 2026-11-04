import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh_src = gc.open_by_key('1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk')
ws_c1 = sh_src.worksheet('Ca 1 - 7 ngay')
print("Ca 1 - 7 ngay row 1-5 formulas:")
for r in ws_c1.get_values('A1:J5', value_render_option='FORMULA'):
    print(r)

