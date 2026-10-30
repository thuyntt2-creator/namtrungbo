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

# 1. Map AM
ws_cocau = sh.worksheet("Cocau")
am_map = {}
for r in ws_cocau.get_all_values()[1:]:
    if len(r) >= 4 and r[1].strip():
        am_map[r[1].strip()] = r[3].strip()

def find_am(bc_name):
    if bc_name in am_map: return am_map[bc_name]
    for k, v in am_map.items():
        if k in bc_name or bc_name in k: return v
    return "Không rõ AM"

# 2. Đọc lượng hàng hôm nay từ tab hàng về (Sheet NTB Vận Hành)
vol_today_map = {}
try:
    sh_ops = gc.open_by_key(SHEET_OPS_ID)
    ws_hv = sh_ops.worksheet('hàng về')
    for r in ws_hv.get_all_values()[1:]:
        if len(r) >= 2:
            k_id = r[0].strip()
            v_raw = r[1].replace(',', '').replace('.', '').strip()
            if v_raw.isdigit():
                vol_today_map[k_id] = int(v_raw)
except Exception as e:
    print(f"Lỗi đọc hàng về: {e}")

# 3. Đọc BC_canh_bao
ws_cb = sh.worksheet("BC_canh_bao")
cb_data = ws_cb.get_all_values()

results = []
for r in cb_data[5:]:
    if not r or len(r) < 4 or not r[3].strip():
        continue
    bc_name = r[3].strip()
    bc_id_str = r[2].strip() if len(r) > 2 else ""
    cb_str = r[18].strip() if len(r) > 18 else ""

    if not cb_str or ("Cảnh báo" not in cb_str and "<" not in cb_str):
        continue

    v_p = r[15].replace(',', '').replace('.', '').strip() if len(r) > 15 else ""
    vol_can_giao_num = int(v_p) if v_p.isdigit() else 0

    vol_today = vol_today_map.get(bc_id_str, vol_today_map.get(bc_name, 0))
    if vol_today == 0:
        vol_today = vol_can_giao_num

    if vol_can_giao_num < 100 or vol_today < 100 or "phú quý" in bc_name.lower():
        continue

    am_name = find_am(bc_name)

    gtc_best_str = r[5].replace('%', '').strip() if len(r) > 5 else ""
    gtc_best = float(gtc_best_str) / 100 if gtc_best_str else 0.5
    target_pct = max(0.50, 0.7 * gtc_best)

    # Tính toán trực tiếp 100% từ BC_canh_bao
    gtc_7d_val = float(r[4].replace('%', '').strip()) / 100 if len(r) > 4 and r[4].replace('%', '').strip() else 0
    vol_gtc_7d = float(r[14].replace(',', '')) if len(r) > 14 and r[14].replace(',', '').isdigit() else 0
    if gtc_7d_val > 0 and vol_gtc_7d > 0:
        total_vol_7d = (vol_gtc_7d * 7) / gtc_7d_val
        vol_6d = total_vol_7d * (6 / 7)
        gtc_6d = (vol_gtc_7d * 7) * (6 / 7)
    else:
        vol_6d, gtc_6d = 0, 0

    req_gtc = round(target_pct * (vol_6d + vol_today) - gtc_6d)
    req_gtc = max(req_gtc, round(0.20 * vol_today), 0)

    is_achievable = req_gtc <= vol_today if vol_today > 0 else False
    pct_needed = round((req_gtc / vol_today) * 100) if vol_today > 0 else 0

    if is_achievable:
        target_val = req_gtc
        note = f"Đạt {pct_needed}% là Thoát Bể"
        is_max = False
    else:
        target_val = vol_today
        note = f"Bể sâu, cần cày thêm ngày (Max {vol_today:,} đơn)"
        is_max = True

    results.append({
        "bc_name": bc_name,
        "id": bc_id_str,
        "am": am_name,
        "vol_today": vol_today,
        "target": target_val,
        "is_achievable": is_achievable,
        "pct_needed": pct_needed,
        "note": note
    })

print(f"Tổng số bưu cục cảnh báo tính được: {len(results)}\n")
for it in results:
    ach_str = "🟢 CƠ HỘI THOÁT" if it['is_achievable'] else "🔴 BỂ SÂU"
    print(f"• {it['bc_name']:28} | AM: {it['am']:20} | Vol: {it['vol_today']:4} | Target: {it['target']:4} đơn | {it['note']:35} | {ach_str}")

