import sys, json
import gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)

sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
print(f"Spreadsheet Title: {sh.title}")

target_ws = None
for ws in sh.worksheets():
    print(f"Worksheet: id={ws.id}, title='{ws.title}', rows={ws.row_count}, cols={ws.col_count}")
    if ws.id == 957775572:
        target_ws = ws

if not target_ws:
    print("Could not find worksheet with gid 957775572, using first or checking matching titles.")
    # check default
else:
    print(f"\n--- Checking Target Worksheet: '{target_ws.title}' (gid={target_ws.id}) ---")
    # Fetch first 25 rows
    # Col J is the 10th column (A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9, J=10, K=11)
    values = target_ws.get_values('A1:O25')
    for i, r in enumerate(values):
        col_j = r[9] if len(r) > 9 else "<NO COL J>"
        # also print first few cols to understand context
        print(f"Row {i+1}: Col J = {repr(col_j)} | Sample: {r[:5]}")
    
    # Also check formulas in col J
    print("\n--- Checking formulas in Col J ---")
    formulas = target_ws.get_values('J1:J25', value_render_option='FORMULA')
    for i, f in enumerate(formulas):
        val = f[0] if len(f) > 0 else ""
        print(f"Row {i+1} Formula: {repr(val)}")

