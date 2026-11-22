import os
import sys
import json
import re
import datetime
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_DIR = r"C:\Users\lap4all\Desktop\New folder"
os.chdir(PROJECT_DIR)

raw_path = 'sheet_truythu.csv'
if not os.path.exists(raw_path):
    print("❌ sheet_truythu.csv not found!")
    sys.exit(1)

df = pd.read_csv(raw_path, low_memory=False)
print(f"Loaded {len(df):,} rows from {raw_path}")

def parse_date(val):
    if not val or pd.isna(val): return None
    s = str(val).strip()
    m = re.search(r'(\d+)\s+thg\s+(\d+),\s+(\d{4})', s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime.datetime(year, month, day)
    return None

def parse_val(v):
    if v is None or pd.isna(v): return 0.0
    s = str(v).strip()
    if not s or s == '-' or s == 'None': return 0.0
    if s.count('.') > 1:
        try:
            return float(s.replace('.', '')) / 1000.0
        except:
            return 0.0
    try:
        return float(s)
    except:
        clean = re.sub(r'[^\d.-]', '', s)
        try:
            return float(clean)
        except:
            return 0.0

col_date = 'Ngày kết luận truy thu'
col_bd = 'Số tiền ban đầu'
col_dc = 'Điều chỉnh (+|-)'
col_da_thu = 'Đã truy thu'
col_ct = 'Cần truy thu thêm'
col_loai = 'Loại truy thu'
col_noi_vp = 'Nơi vi phạm'
col_nv = 'Nhân viên'
col_cv = 'Chức vụ'
col_ma_tt = 'Mã truy thu'
col_ticket = 'Mã ticket'
col_id_vp = 'ID Nơi vi phạm'

df['date'] = df[col_date].apply(parse_date)
df = df[df['date'].notna()].copy()
df['iso_year'] = df['date'].apply(lambda d: d.isocalendar()[0])
df['iso_week'] = df['date'].apply(lambda d: d.isocalendar()[1])

# Determine weeks dynamically: latest week in 2026
weeks_2026 = sorted(df[df['iso_year'] == 2026]['iso_week'].unique())
curr_num = weeks_2026[-1] if weeks_2026 else 45
prev_num = curr_num - 1

curr_start = datetime.date.fromisocalendar(2026, curr_num, 1)
curr_end = datetime.date.fromisocalendar(2026, curr_num, 7)
prev_start = datetime.date.fromisocalendar(2026, prev_num, 1)
prev_end = datetime.date.fromisocalendar(2026, prev_num, 7)

prev_label = f"Tuần W{prev_num} ({prev_start.strftime('%d/%m')} – {prev_end.strftime('%d/%m')})"
curr_label = f"Tuần W{curr_num} ({curr_start.strftime('%d/%m')} – {curr_end.strftime('%d/%m')})"

w_prev = df[(df['iso_year'] == 2026) & (df['iso_week'] == prev_num)].copy()
w_curr = df[(df['iso_year'] == 2026) & (df['iso_week'] == curr_num)].copy()

print(f"Comparing {prev_label} ({len(w_prev):,} records) vs {curr_label} ({len(w_curr):,} records)")

# Convert values to VND (sheet values are in nghìn đồng, so * 1000)
for w in [w_prev, w_curr]:
    w['ban_dau'] = w[col_bd].apply(parse_val) * 1000.0
    w['dieu_chinh'] = w[col_dc].apply(parse_val) * 1000.0
    w['da_thu'] = w[col_da_thu].apply(parse_val) * 1000.0
    w['can_thu'] = w[col_ct].apply(parse_val) * 1000.0

# Mapping AM & Province from co_cau_ntb.csv
cc_wh_am = {}
cc_wh_tinh = {}
cc_bc_am = {}
cc_bc_tinh = {}

if os.path.exists('co_cau_ntb.csv'):
    cc = pd.read_csv('co_cau_ntb.csv', encoding='utf-8')
    for _, row in cc.iterrows():
        wh = str(int(float(row['warehouse_id']))) if pd.notna(row['warehouse_id']) else ''
        bc = str(row['Bưu cục']).strip() if pd.notna(row['Bưu cục']) else ''
        am = str(row['AM']).strip() if pd.notna(row['AM']) else ''
        prov = str(row['Tỉnh']).strip() if pd.notna(row['Tỉnh']) else ''
        if wh:
            cc_wh_am[wh] = am
            cc_wh_tinh[wh] = prov
        if bc:
            cc_bc_am[bc] = am
            cc_bc_tinh[bc] = prov

def clean_wh_id(v):
    try: return str(int(float(v)))
    except: return ''

def get_province_fallback(bc):
    bc = str(bc)
    if '(KHO)' in bc: return 'Khánh Hòa'
    if '(LDO)' in bc: return 'Lâm Đồng'
    if '(DNO)' in bc: return 'Đắk Nông'
    if '(BTH)' in bc: return 'Bình Thuận'
    if '(NTH)' in bc: return 'Ninh Thuận'
    return 'Khác'

for w in [w_prev, w_curr]:
    w['wh_clean'] = w[col_id_vp].apply(clean_wh_id)
    w['bc_clean'] = w[col_noi_vp].astype(str).str.strip()
    w['AM'] = w['wh_clean'].map(cc_wh_am).fillna(w['bc_clean'].map(cc_bc_am)).fillna('Chưa gán')
    w['Tỉnh'] = w['wh_clean'].map(cc_wh_tinh).fillna(w['bc_clean'].map(cc_bc_tinh))
    w['Tỉnh'] = w.apply(lambda r: r['Tỉnh'] if pd.notna(r['Tỉnh']) and r['Tỉnh'] not in ['', 'nan'] else get_province_fallback(r[col_noi_vp]), axis=1)

# 1. Summary
rec_p = len(w_prev)
rec_c = len(w_curr)
diff_rec = rec_c - rec_p
diff_rec_pct = round(diff_rec / rec_p * 100, 1) if rec_p else 0

tk_p = int(w_prev[col_ticket].nunique())
tk_c = int(w_curr[col_ticket].nunique())
diff_tk = tk_c - tk_p
diff_tk_pct = round(diff_tk / tk_p * 100, 1) if tk_p else 0

bd_p = float(w_prev['ban_dau'].sum())
bd_c = float(w_curr['ban_dau'].sum())
diff_bd = bd_c - bd_p
diff_bd_pct = round(diff_bd / bd_p * 100, 1) if bd_p else 0

dc_p = float(w_prev['dieu_chinh'].sum())
dc_c = float(w_curr['dieu_chinh'].sum())
diff_dc = dc_c - dc_p

ct_p = float(w_prev['can_thu'].sum())
ct_c = float(w_curr['can_thu'].sum())
diff_ct = ct_c - ct_p
diff_ct_pct = round(diff_ct / ct_p * 100, 1) if ct_p else 0

print(f"Summary: Records={rec_c} (diff {diff_rec}), Tickets={tk_c} (diff {diff_tk}), BanDau={bd_c/1e6:.1f}Tr, CanThu={ct_c/1e6:.1f}Tr (diff {diff_ct/1e6:+.1f}Tr | {diff_ct_pct:+.1f}%)")

# 2. Comparison by Loại
loai_p = w_prev.groupby(col_loai).agg(don_p=(col_ma_tt, 'count'), bd_p=('ban_dau', 'sum'), ct_p=('can_thu', 'sum'))
loai_c = w_curr.groupby(col_loai).agg(don_c=(col_ma_tt, 'count'), bd_c=('ban_dau', 'sum'), ct_c=('can_thu', 'sum'))
loai_cmp = pd.concat([loai_p, loai_c], axis=1).fillna(0)
loai_cmp['diff_don'] = loai_cmp['don_c'] - loai_cmp['don_p']
loai_cmp['diff_ct'] = loai_cmp['ct_c'] - loai_cmp['ct_p']
loai_cmp = loai_cmp.sort_values('ct_c', ascending=False)

top_loai_strs = []
for idx, r in loai_cmp.head(3).iterrows():
    top_loai_strs.append(f"<em>{idx}</em> ({r['ct_c']/1e6:.1f} Tr ₫ | {int(r['don_c']):,} đơn)")
top_loai_desc = ", ".join(top_loai_strs)

by_loai_list = []
for idx, r in loai_cmp.iterrows():
    loai_name = str(idx)
    don_prev = int(r['don_p'])
    don_curr = int(r['don_c'])
    diff_don = int(r['diff_don'])
    pct_don_diff = f"{round((diff_don / don_prev * 100), 1):+0.1f}%" if don_prev > 0 else ("+100%" if don_curr > 0 else "0%")

    ct_prev = float(r['ct_p'])
    ct_curr = float(r['ct_c'])
    diff_ct_val = float(r['diff_ct'])
    pct_ct_diff = f"{round((diff_ct_val / ct_prev * 100), 1):+0.1f}%" if ct_prev > 0 else ("+100%" if ct_curr > 0 else "0%")

    eval_badge = "-"
    if ct_curr >= 15e6 or diff_ct_val >= 10e6:
        eval_badge = "🚨 Tăng mạnh (Bất thường)"
    elif diff_ct_val > 3e6:
        eval_badge = "⚠️ Cảnh báo tăng"
    elif diff_ct_val < -3e6:
        eval_badge = "🟢 Giảm tốt"
    elif ct_curr == 0 and ct_prev == 0:
        eval_badge = "🟢 0 ₫"

    note = "Vi phạm nghiệp vụ"
    if 'Backlog' in loai_name:
        note = "Tồn đọng vận hành bưu cục"
    elif 'hư hỏng' in loai_name.lower():
        note = "Hàng hóa hư hỏng trong quá trình vận chuyển"
    elif 'chiếm dụng' in loai_name.lower():
        note = "Gian lận/chiếm dụng tiền COD hoặc bưu gửi"
    elif 'quá hạn' in loai_name.lower():
        note = "Trễ toàn trình vượt ngưỡng cho phép"

    by_loai_list.append({
        "loai": loai_name,
        "don_prev": don_prev,
        "don_curr": don_curr,
        "diff_don": diff_don,
        "pct_don_diff": pct_don_diff,
        "can_thu_prev": ct_prev,
        "can_thu_curr": ct_curr,
        "diff_can_thu": diff_ct_val,
        "pct_can_thu_diff": pct_ct_diff,
        "eval": eval_badge,
        "ghi_chu": note
    })

# 3. Comparison by AM
am_p = w_prev.groupby('AM').agg(tk_p=(col_ticket, 'nunique'), rec_p=(col_ma_tt, 'count'), bd_p=('ban_dau', 'sum'), ct_p=('can_thu', 'sum'))
am_c = w_curr.groupby('AM').agg(tk_c=(col_ticket, 'nunique'), rec_c=(col_ma_tt, 'count'), bd_c=('ban_dau', 'sum'), ct_c=('can_thu', 'sum'))
am_cmp = pd.concat([am_p, am_c], axis=1).fillna(0)
am_cmp['diff_tk'] = am_cmp['tk_c'] - am_cmp['tk_p']
am_cmp['diff_ct'] = am_cmp['ct_c'] - am_cmp['ct_p']
am_cmp = am_cmp.sort_values('ct_c', ascending=False)

top_am_strs = []
for idx, r in am_cmp.head(5).iterrows():
    if idx != 'Chưa gán':
        top_am_strs.append(f"<strong>{idx}</strong> ({r['ct_c']/1e6:.1f} Tr ₫ | {int(r['tk_c']):,} ticket)")
top_am_desc = ", ".join(top_am_strs[:4])

am_top_bc = {}
for am_name, grp in w_curr.groupby('AM'):
    bc_sum = grp.groupby(col_noi_vp)['can_thu'].sum().sort_values(ascending=False)
    if not bc_sum.empty:
        top_bc_name = bc_sum.index[0]
        top_bc_val = bc_sum.iloc[0]
        am_top_bc[am_name] = f"{top_bc_name} ({top_bc_val/1e6:.1f} Tr)"

by_am_list = []
for idx, r in am_cmp.iterrows():
    am_name = str(idx)
    tk_prev = int(r['tk_p'])
    tk_curr = int(r['tk_c'])
    am_diff_tk = int(r['diff_tk'])
    pct_tk_diff = f"{round((am_diff_tk / tk_prev * 100), 1):+0.1f}%" if tk_prev > 0 else ("+100%" if tk_curr > 0 else "0%")

    ct_prev = float(r['ct_p'])
    ct_curr = float(r['ct_c'])
    diff_ct_val = float(r['diff_ct'])
    pct_ct_diff = f"{round((diff_ct_val / ct_prev * 100), 1):+0.1f}%" if ct_prev > 0 else ("+100%" if ct_curr > 0 else "0%")

    level = "🟢 Tốt"
    if ct_curr >= 10e6 or diff_ct_val >= 8e6:
        level = "🚨 Rất cao (≥10 Tr)"
    elif ct_curr >= 5e6 or diff_ct_val >= 3e6:
        level = "⚠️ Cần kiểm soát (5-10 Tr)"
    elif tk_curr >= 40:
        level = "⚠️ Nhiều ticket (≥40)"

    by_am_list.append({
        "am": am_name,
        "ticket_prev": tk_prev,
        "ticket_curr": tk_curr,
        "diff_ticket": am_diff_tk,
        "pct_ticket_diff": pct_tk_diff,
        "can_thu_prev": ct_prev,
        "can_thu_curr": ct_curr,
        "diff_can_thu": diff_ct_val,
        "pct_can_thu_diff": pct_ct_diff,
        "level": level,
        "top_bc_culprit": am_top_bc.get(am_name, "-")
    })

# 4. Comparison by Province
prov_p = w_prev.groupby('Tỉnh').agg(don_p=(col_ma_tt, 'count'), ct_p=('can_thu', 'sum'))
prov_c = w_curr.groupby('Tỉnh').agg(don_c=(col_ma_tt, 'count'), ct_c=('can_thu', 'sum'))
prov_cmp = pd.concat([prov_p, prov_c], axis=1).fillna(0)
prov_cmp['diff_don'] = prov_cmp['don_c'] - prov_cmp['don_p']
prov_cmp['diff_ct'] = prov_cmp['ct_c'] - prov_cmp['ct_p']
prov_cmp = prov_cmp.sort_values('ct_c', ascending=False)

by_province_list = []
for idx, r in prov_cmp.iterrows():
    p_name = str(idx)
    by_province_list.append({
        "tinh": p_name,
        "don_prev": int(r['don_p']),
        "don_curr": int(r['don_c']),
        "diff_don": int(r['diff_don']),
        "can_thu_prev": float(r['ct_p']),
        "can_thu_curr": float(r['ct_c']),
        "diff_can_thu": float(r['diff_ct'])
    })

# 5. Top 30 BC Comparison
bc_p = w_prev.groupby([col_noi_vp, 'AM', 'Tỉnh']).agg(don_p=(col_ticket, 'nunique'), ct_p=('can_thu', 'sum'))
bc_c = w_curr.groupby([col_noi_vp, 'AM', 'Tỉnh']).agg(don_c=(col_ticket, 'nunique'), bd_c=('ban_dau', 'sum'), ct_c=('can_thu', 'sum'))
bc_cmp = pd.concat([bc_p, bc_c], axis=1).fillna(0).reset_index()
bc_cmp['diff_don'] = bc_cmp['don_c'] - bc_cmp['don_p']
bc_cmp['diff_ct'] = bc_cmp['ct_c'] - bc_cmp['ct_p']
bc_cmp = bc_cmp.sort_values('ct_c', ascending=False)

top_bc_list = []
for _, r in bc_cmp.head(30).iterrows():
    ct_p_val = float(r['ct_p'])
    ct_c_val = float(r['ct_c'])
    diff_ct_val = float(r['diff_ct'])
    diff_don_val = int(r['don_c'] - r['don_p'])
    top_bc_list.append({
        "bc": r[col_noi_vp],
        "am": r['AM'],
        "tinh": r['Tỉnh'],
        "don_prev": int(r['don_p']),
        "don_curr": int(r['don_c']),
        "diff_don": diff_don_val,
        "can_thu_prev": ct_p_val,
        "can_thu_curr": ct_c_val,
        "diff_can_thu": diff_ct_val,
        "pct_can_thu_diff": f"{round((diff_ct_val / ct_p_val * 100), 1):+0.1f}%" if ct_p_val > 0 else ("+100%" if ct_c_val > 0 else "0%")
    })

ct_trend = f"tăng +{diff_ct/1e6:,.1f} Tr ₫ (+{diff_ct_pct:0.1f}%)" if diff_ct >= 0 else f"giảm {abs(diff_ct)/1e6:,.1f} Tr ₫ ({diff_ct_pct:0.1f}%)"
bd_trend = f"tăng {diff_bd_pct:+0.1f}%" if diff_bd >= 0 else f"giảm {abs(diff_bd_pct):0.1f}%"
tk_trend = f"tăng +{diff_tk:,} ticket" if diff_tk >= 0 else f"giảm {abs(diff_tk):,} ticket"

# Individual top AMs by responsible employee (e.g. Hồng Bích Nga 8.5 Tr)
def clean_nv(v):
    return re.sub(r'^\d+[\s\-]*', '', str(v or '')).strip()

w_curr['nv_clean'] = w_curr[col_nv].apply(clean_nv)
top_nv_sum = w_curr.groupby('nv_clean')['can_thu'].sum().sort_values(ascending=False)
top_nv_name = top_nv_sum.index[0] if not top_nv_sum.empty else ""
top_nv_val = top_nv_sum.iloc[0] if not top_nv_sum.empty else 0.0

banner_desc = (
    f"• <strong>Tổng quan so sánh 2 tuần ({prev_label} vs {curr_label}):</strong> Tuần W{curr_num} phát sinh <strong>{tk_c:,} ticket</strong> "
    f"({rec_c:,} bản ghi, {tk_trend}, {diff_tk_pct:+0.1f}% WoW so với {tk_p:,} ticket của W{prev_num}). "
    f"Số tiền ban đầu <strong>{bd_c/1e6:,.1f} Tr ₫</strong> ({bd_trend} WoW so với {bd_p/1e6:,.1f} Tr ₫ của W{prev_num}). "
    f"Cần truy thu thêm <strong>{ct_c/1e6:,.1f} Tr ₫</strong> ({ct_trend} so với {ct_p/1e6:,.1f} Tr ₫ của W{prev_num}).<br>"
    f"• <strong>Các loại truy thu trọng điểm:</strong> {top_loai_desc}.<br>"
    f"• <strong>Top quản lý / AM có số tiền truy thu lớn nhất:</strong> {top_am_desc} (Top cá nhân trách nhiệm: <strong>{top_nv_name}</strong> {top_nv_val/1e6:,.1f} Tr ₫).<br>"
    f"<em>Ghi chú: Toàn bộ {ct_c/1e6:,.1f} Tr ₫ của Tuần W{curr_num} hiện đang được kiểm soát đôn đốc xử lý theo kết luận truy thu.</em>"
)

summary = {
    "prev_label": prev_label,
    "curr_label": curr_label,
    "total_records_prev": rec_p,
    "total_records_curr": rec_c,
    "diff_records": diff_rec,
    "diff_records_pct": f"{diff_rec_pct:+0.1f}%",
    "ticket_prev": tk_p,
    "ticket_curr": tk_c,
    "diff_ticket": diff_tk,
    "diff_ticket_pct": f"{diff_tk_pct:+0.1f}%",
    "ban_dau_prev": bd_p,
    "ban_dau_curr": bd_c,
    "diff_ban_dau": diff_bd,
    "diff_ban_dau_pct": f"{diff_bd_pct:+0.1f}%",
    "dieu_chinh_prev": dc_p,
    "dieu_chinh_curr": dc_c,
    "diff_dieu_chinh": diff_dc,
    "can_thu_prev": ct_p,
    "can_thu_curr": ct_c,
    "diff_can_thu": diff_ct,
    "diff_can_thu_pct": f"{diff_ct_pct:+0.1f}%",
    "banner_desc": banner_desc
}

truy_thu_report_obj = {
    "summary": summary,
    "total_records": rec_c,
    "total_ban_dau": bd_c,
    "total_dieu_chinh": dc_c,
    "total_can_thu": ct_c,
    "by_loai": by_loai_list,
    "by_am": by_am_list,
    "by_province": by_province_list,
    "top_bc": top_bc_list
}

with open('data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

d['truy_thu_report'] = truy_thu_report_obj

# Also update d['truy_thu'] for summary tiles in Tab 1
d['truy_thu'] = {
    "summary": {
        "val_curr_tr": round(ct_c / 1e6, 1),
        "val_prev_tr": round(ct_p / 1e6, 1),
        "diff_tr": round(diff_ct / 1e6, 1),
        "diff_pct": round(diff_ct_pct, 1),
        "ticket_curr": tk_c,
        "ticket_prev": tk_p,
        "top_am": top_nv_name,
        "top_am_val": round(top_nv_val / 1e6, 1)
    }
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

with open('data.js', 'w', encoding='utf-8') as f:
    f.write('window.DASHBOARD_DATA = ' + json.dumps(d, ensure_ascii=False, indent=2) + ';\n')
    f.write('window.DATA = window.DASHBOARD_DATA;\n')
    f.write('const REPORT_DATA = window.DASHBOARD_DATA;\n')

print("✅ SUCCESS: Saved truy_thu_report and truy_thu into data.json and data.js!")
print(f"Summary: {summary['prev_label']} vs {summary['curr_label']}")
print(f"Can thu: W44 = {ct_p/1e6:.1f} Tr -> W45 = {ct_c/1e6:.1f} Tr (Diff: {diff_ct/1e6:+.1f} Tr | {diff_ct_pct:+.1f}%)")
print(f"Tickets: W44 = {tk_p} -> W45 = {tk_c}")
