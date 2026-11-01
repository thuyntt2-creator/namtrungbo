import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

sh = gc.open_by_key('14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo')
for ws in sh.worksheets():
    print(f"Worksheet: {ws.title}")
    # Search for 554 or 331
    try:
        cells = ws.findall('554')
        if cells:
            for c in cells[:3]:
                print(f"  Found 554 in {ws.title} at {c.address}: row {ws.row_values(c.row)[:5]}")
    except:
        pass

