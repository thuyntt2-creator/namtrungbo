import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_lt = sh.worksheet("luu_tru")
lt_data = ws_lt.get_all_values()

print("Checking Trường Xuân in luu_tru:")
count = 0
for r in lt_data[1:]:
    if 'Trường Xuân' in str(r) or '22086000' in str(r):
        print(f"Date: {r[0]} | Vùng: {r[1]} | ID: {r[3]} | Name: '{r[4]}' | Vol: {r[16] if len(r)>16 else ''} | GTC: {r[9] if len(r)>9 else ''}")
        count += 1
        if count >= 10:
            break
if count == 0:
    print("NO ROWS FOUND for Trường Xuân or 22086000 in luu_tru!")

