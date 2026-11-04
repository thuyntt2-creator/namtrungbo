import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh_src = gc.open_by_key('1odUPX5mWpUYUUQOrhX_k8kXWV7drMUdQ58DRwgSQNS8')
for title in ['Bưu cục cảnh báo - 50%', 'raw_buu_cuc_canh_bao', 'raw_buu_cuc_canh_bao_2']:
    try:
        ws = sh_src.worksheet(title)
        print(f"Sheet '{title}' row 1-5:")
        for r in ws.get_values('A1:L5'):
            print("  ", r)
    except Exception as e:
        print(f"Error reading {title}:", e)

