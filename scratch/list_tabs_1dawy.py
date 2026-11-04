import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh_src = gc.open_by_key('1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk')
for ws in sh_src.worksheets():
    print(f"  {ws.title} ({ws.id}) rows={ws.row_count}")

