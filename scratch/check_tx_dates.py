import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_lt = sh.worksheet("luu_tru")
lt_data = ws_lt.get_all_values()

tx_dates = []
for r in lt_data[1:]:
    if '22086000' in str(r) or 'Trường Xuân' in str(r):
        tx_dates.append(r[0])
print("All dates for Trường Xuân:", tx_dates[-20:])

