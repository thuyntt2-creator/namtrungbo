import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')

ws_raw = sh.worksheet('raw')
print("Tab raw A1 formula:", ws_raw.acell('A1', value_render_option='FORMULA').value)
print("Tab raw A2 formula:", ws_raw.acell('A2', value_render_option='FORMULA').value)

# Check Datatoday
try:
    ws_dt = sh.worksheet('Datatoday')
    print("\nTab Datatoday row 1:", ws_dt.row_values(1)[:10])
    print("Tab Datatoday A1 formula:", ws_dt.acell('A1', value_render_option='FORMULA').value)
    print("Tab Datatoday A2 formula:", ws_dt.acell('A2', value_render_option='FORMULA').value)
    dates_dt = set(ws_dt.col_values(4)[1:])
    print("Distinct dates in Datatoday Col D:", dates_dt)
except Exception as e:
    print("Datatoday error:", e)

# Check BC_canh_bao
try:
    ws_bc = sh.worksheet('BC_canh_bao')
    print("\nTab BC_canh_bao row 4:", ws_bc.row_values(4)[:15])
    print("Tab BC_canh_bao row 5:", ws_bc.row_values(5)[:15])
except Exception as e:
    print("BC_canh_bao error:", e)

