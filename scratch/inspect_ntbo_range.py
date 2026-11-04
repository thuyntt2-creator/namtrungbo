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

# Get all values in Col A, B, C to know how many bưu cục
col_c = ws_ntbo.col_values(3) # Tên BC
print(f"Total rows with Tên BC (Col C): {len(col_c)}")
for i in range(4, min(15, len(col_c))):
    print(f"Row {i+1}: {col_c[i]}")

# Find last row
last_row = len(col_c)
print(f"Last row index: {last_row}")
print(f"Last row content: {ws_ntbo.row_values(last_row)[:5]}")

# Check formulas in row 6 cols D:O
f_row6 = ws_ntbo.get_values('D6:O6', value_render_option='FORMULA')[0]
print("\nFormulas in Row 6 (D:O):")
for col_idx, f in enumerate(f_row6):
    col_letter = chr(ord('D') + col_idx)
    print(f"  Col {col_letter}: {f}")

