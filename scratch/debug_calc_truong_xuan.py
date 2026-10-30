import sys, os, json, unicodedata
from datetime import datetime
import gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')

creds = Credentials.from_authorized_user_file('authorized_user.json', ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(creds)

SHEET_ID = "1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec"
SHEET_OPS_ID = "14cN4YAf01NqKtREtmhBngRP58OCdgby-PjVoixVlpZo"

sh = gc.open_by_key(SHEET_ID)

# 2. Đọc lượng hàng hôm nay từ tab hàng về (Sheet NTB Vận Hành)
vol_today_map = {}
sh_ops = gc.open_by_key(SHEET_OPS_ID)
ws_hv = sh_ops.worksheet('hàng về')
for r in ws_hv.get_all_values()[1:]:
    if len(r) >= 2:
        k_id = r[0].strip()
        v_raw = r[1].replace(',', '').replace('.', '').strip()
        if v_raw.isdigit():
            vol_today_map[k_id] = int(v_raw)

# 3. Đọc dữ liệu lịch sử từ tab luu_tru
ws_lt = sh.worksheet("luu_tru")
lt_data = ws_lt.get_all_values()
ntb_dates = []
for r in lt_data[1:]:
    if len(r) > 1 and r[1].strip() == 'NTB':
        d = r[0].strip()
        if d and d not in ntb_dates:
            ntb_dates.append(d)

def parse_date_obj(d_str):
    for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try: return datetime.strptime(d_str, fmt)
        except ValueError: pass
    return datetime(1970, 1, 1)

sorted_ntb_dates = sorted(ntb_dates, key=parse_date_obj)
dates_6d = sorted_ntb_dates[-6:] if len(sorted_ntb_dates) >= 6 else sorted_ntb_dates
print(f"6 ngày gần nhất: {dates_6d}")

history_6d = {}
for r in lt_data[1:]:
    if len(r) > 19 and r[1].strip() == 'NTB':
        d = r[0].strip()
        b_name = r[4].strip()
        if d in dates_6d:
            v_tong = float(r[16].replace(',', '')) if len(r) > 16 and r[16].replace(',', '').isdigit() else 0
            v_gtc = float(r[9].replace(',', '')) if len(r) > 9 and r[9].replace(',', '').isdigit() else 0
            h = history_6d.setdefault(b_name, {'vol_6d': 0, 'gtc_6d': 0, 'dates': set()})
            h['vol_6d'] += v_tong
            h['gtc_6d'] += v_gtc
            h['dates'].add(d)

ws_cb = sh.worksheet("BC_canh_bao")
cb_data = ws_cb.get_all_values()

for r in cb_data[5:]:
    if not r or len(r) < 4 or not r[3].strip():
        continue
    bc_name = r[3].strip()
    if 'Trường Xuân' not in bc_name and 'Quảng Khê' not in bc_name:
        continue
    bc_id_str = r[2].strip() if len(r) > 2 else ""

    vol_today = vol_today_map.get(bc_id_str, vol_today_map.get(bc_name, 0))
    v_p = r[15].replace(',', '').replace('.', '').strip() if len(r) > 15 else ""
    v_p_num = int(v_p) if v_p.isdigit() else 0

    gtc_best_str = r[5].replace('%', '').strip() if len(r) > 5 else ""
    gtc_best = float(gtc_best_str) / 100 if gtc_best_str else 0.5
    target_pct = max(0.50, 0.7 * gtc_best)

    h6 = history_6d.get(bc_name, {'vol_6d': 0, 'gtc_6d': 0, 'dates': set()})
    vol_6d = h6['vol_6d']
    gtc_6d = h6['gtc_6d']

    req_gtc = round(target_pct * (vol_6d + vol_today) - gtc_6d)
    req_gtc = max(req_gtc, round(0.20 * vol_today), 0)

    print(f"\n--- {bc_name} (ID: {bc_id_str}) ---")
    print(f"vol_today_map: {vol_today_map.get(bc_id_str)} | r[15] vol_can_giao: {v_p_num}")
    print(f"vol_today used: {vol_today}")
    print(f"gtc_best: {gtc_best_str} -> target_pct: {target_pct}")
    print(f"dates found in luu_tru: {h6['dates']}")
    print(f"vol_6d: {vol_6d}, gtc_6d: {gtc_6d}")
    print(f"req_gtc calculated: {req_gtc}")

