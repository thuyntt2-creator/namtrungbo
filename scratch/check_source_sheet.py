import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
try:
    sh_src = gc.open_by_key('1odUPX5mWpUYUUQOrhX_k8kXWV7drMUdQ58DRwgSQNS8')
    print("Opened source sheet:", sh_src.title)
    for ws in sh_src.worksheets():
        print(f"  {ws.title} ({ws.id})")
except Exception as e:
    print("Error opening source sheet:", e)

