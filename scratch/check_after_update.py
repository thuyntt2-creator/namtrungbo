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
headers = ws_ntbo.row_values(5)
print("=== HEADERS ROW 5 ===")
print(headers[:15])

print("\n=== TOP 15 ROWS IN NTBo (Cols A-O) ===")
rows = ws_ntbo.get_values('A6:O20')
for i, r in enumerate(rows):
    bc_name = r[2] if len(r) > 2 else ""
    col_j = r[9] if len(r) > 9 else ""
    pct_7d = r[10] if len(r) > 10 else ""
    status = r[13] if len(r) > 13 else ""
    print(f"Row {i+6:2d}: {bc_name:<30} | Col J (03/11): {col_j:<8} | %GTC 7D: {pct_7d:<8} | Status: {status}")

# Check total alerts in NTBo
total_alert = ws_ntbo.acell('J2').value
print(f"\nTổng số bưu cục cảnh báo (Cell J2): {total_alert}")

