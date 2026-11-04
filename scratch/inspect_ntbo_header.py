import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_ntbo = sh.worksheet('NTBo')

print("Rows 1 to 5 values:")
for i in range(1, 6):
    print(f"Row {i}:", ws_ntbo.row_values(i))

print("\nRows 1 to 5 formulas:")
formulas = ws_ntbo.get_values('A1:O5', value_render_option='FORMULA')
for i, r in enumerate(formulas):
    print(f"Row {i+1} formula:", r)

