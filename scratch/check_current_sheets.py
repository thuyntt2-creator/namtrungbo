import sys, gspread
from google.oauth2.credentials import Credentials
sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

# 1. Check tab hàng về
sh_ops = gc.open_by_key('14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo')
ws_hv = sh_ops.worksheet('hàng về')
rows_hv = ws_hv.get_all_values()
print("=== TAB HÀNG VỀ (14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo) ===")
for r in rows_hv:
    if len(r) >= 2 and ('22086000' in r[0] or '21364000' in r[0] or 'Trường Xuân' in str(r) or 'Quảng Khê' in str(r)):
        print(r)

# 2. Check tab BC_canh_bao
sh_cb = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_cb = sh_cb.worksheet('BC_canh_bao')
rows_cb = ws_cb.get_all_values()
print("\n=== TAB BC_CANH_BAO (1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec) ===")
print("Header Col 15 (P):", rows_cb[3][15] if len(rows_cb)>3 else "")
for r in rows_cb[5:]:
    if len(r) > 3 and ('Trường Xuân' in r[3] or 'Quảng Khê' in r[3]):
        print(f"BC: {r[3]} | ID: {r[2]} | Col E (%GTC 7D): {r[4]} | Col F (GTC Best): {r[5]} | Col O (GTC 7D): {r[14]} | Col P (Vol 15): {r[15]} | Col S (Warning): {r[18]}")

