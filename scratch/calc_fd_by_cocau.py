import openpyxl, datetime
import pandas as pd
import json

print("1. Loading cocau...")
wb = openpyxl.load_workbook(r'C:\Users\lap4all\Desktop\New folder\report.xlsx', data_only=True)
ws_cocau = wb['cocau']

# Map BC -> (Tỉnh, Họ tên AM, AM Code)
bc_to_am = {}
for r in ws_cocau.iter_rows(min_row=2, values_only=True):
    bc_name = r[1]
    tinh = r[3]
    am_name = r[4]
    am_code = r[5]
    if bc_name:
        bc_to_am[str(bc_name).strip()] = {
            'tinh': str(tinh).strip() if tinh else '',
            'am_name': str(am_name).strip() if am_name else '',
            'am_code': str(am_code).strip() if am_code else ''
        }

print(f"Loaded {len(bc_to_am)} bưu cục from cocau.")

print("2. Loading sheet FD...")
ws_fd = wb['FD']

fd_rows = []
for r in ws_fd.iter_rows(min_row=2, max_col=8, values_only=True):
    dt = r[0]
    if dt is None: continue
    if not isinstance(dt, datetime.datetime):
        try:
            dt = datetime.datetime.strptime(str(dt)[:10], '%Y-%m-%d')
        except:
            continue
    iso_year, iso_week, _ = dt.isocalendar()
    if iso_year != 2026 or iso_week not in (44, 45):
        continue
    
    bc = str(r[3]).strip() if r[3] else ''
    ctype = str(r[4]).strip().upper() if r[4] else ''
    try:
        tot = float(r[5] or 0)
        ret = float(r[6] or 0)
    except:
        tot = 0
        ret = 0
        
    am_raw = str(r[7]).strip() if r[7] else ''
    
    # Use cocau mapping if available, else fallback to am_raw
    mapping = bc_to_am.get(bc, {})
    am_code = mapping.get('am_code') or am_raw
    am_name = mapping.get('am_name') or am_raw
    tinh = mapping.get('tinh') or str(r[1]).strip()
    
    is_tts = 'TTS' in ctype
    
    fd_rows.append({
        'date': dt,
        'week': iso_week,
        'bc': bc,
        'tinh': tinh,
        'am_code': am_code,
        'am_name': am_name,
        'client_type': ctype,
        'is_tts': is_tts,
        'tot': tot,
        'ret': ret
    })

wb.close()
df = pd.DataFrame(fd_rows)
print(f"Loaded {len(df)} rows for W44 and W45.")

# Summary by AM
print("\n=== AM CALCULATION (MAPPED BY COCAU) ===")
ams = sorted(df['am_name'].unique())
am_summary = []

for am in ams:
    df_am = df[df['am_name'] == am]
    am_code = df_am['am_code'].iloc[0] if len(df_am) > 0 else am
    
    # W44
    w44 = df_am[df_am['week'] == 44]
    w44_tot = w44['tot'].sum()
    w44_ret = w44['ret'].sum()
    rate_w44 = (w44_ret / w44_tot) if w44_tot > 0 else None
    
    w44_tts = w44[w44['is_tts']]
    w44_tts_tot = w44_tts['tot'].sum()
    w44_tts_ret = w44_tts['ret'].sum()
    rate_tts_w44 = (w44_tts_ret / w44_tts_tot) if w44_tts_tot > 0 else None
    
    # W45
    w45 = df_am[df_am['week'] == 45]
    w45_tot = w45['tot'].sum()
    w45_ret = w45['ret'].sum()
    rate_w45 = (w45_ret / w45_tot) if w45_tot > 0 else None
    
    w45_tts = w45[w45['is_tts']]
    w45_tts_tot = w45_tts['tot'].sum()
    w45_tts_ret = w45_tts['ret'].sum()
    rate_tts_w45 = (w45_tts_ret / w45_tts_tot) if w45_tts_tot > 0 else None
    
    diff_full = (rate_w45 - rate_w44) if (rate_w45 is not None and rate_w44 is not None) else None
    diff_tts = (rate_tts_w45 - rate_tts_w44) if (rate_tts_w45 is not None and rate_tts_w44 is not None) else None
    
    am_summary.append({
        'am': am_code,
        'am_name': am,
        'vol_full': int(w45_tot),
        'ret_full': int(w45_ret),
        'rate_full': round(rate_w45, 4) if rate_w45 is not None else None,
        'rate_full_prev': round(rate_w44, 4) if rate_w44 is not None else None,
        'diff_full': round(diff_full, 4) if diff_full is not None else None,
        'vol_tts': int(w45_tts_tot),
        'ret_tts': int(w45_tts_ret),
        'rate_tts': round(rate_tts_w45, 4) if rate_tts_w45 is not None else None,
        'rate_tts_prev': round(rate_tts_w44, 4) if rate_tts_w44 is not None else None,
        'diff_tts': round(diff_tts, 4) if diff_tts is not None else None,
        'rate_fd': round(rate_w45, 4) if rate_w45 is not None else None,
        'total_orders': int(w45_tot),
        'return_orders': int(w45_ret)
    })

# Sort by rate_full descending
am_summary.sort(key=lambda x: x['rate_full'] if x['rate_full'] is not None else -1, reverse=True)
for i, r in enumerate(am_summary, 1):
    r['stt'] = i
    w44_s = f"{r['rate_full_prev']*100:.2f}%" if r['rate_full_prev'] is not None else "None"
    w45_s = f"{r['rate_full']*100:.2f}%" if r['rate_full'] is not None else "None"
    diff_s = f"{r['diff_full']*100:+.2f}%p" if r['diff_full'] is not None else "None"
    print(f"{i:2d}. {r['am_name']:25s} ({r['am']:10s}): W44={w44_s:7s} | W45={w45_s:7s} | Δ={diff_s:7s} | Vol={r['vol_full']}")

# Summary by Bưu Cục
print("\n=== TOP BƯU CỤC W45 FD ===")
w45_total_ret_all = df[df['week'] == 45]['ret'].sum()

bc_summary = []
bcs = df[df['week'] == 45]['bc'].unique()
for bc in bcs:
    df_bc = df[df['bc'] == bc]
    am_name = df_bc['am_name'].iloc[0]
    am_code = df_bc['am_code'].iloc[0]
    
    w44 = df_bc[df_bc['week'] == 44]
    w44_tot = w44['tot'].sum()
    w44_ret = w44['ret'].sum()
    rate_w44 = (w44_ret / w44_tot) if w44_tot > 0 else None
    
    w45 = df_bc[df_bc['week'] == 45]
    w45_tot = w45['tot'].sum()
    w45_ret = w45['ret'].sum()
    rate_w45 = (w45_ret / w45_tot) if w45_tot > 0 else None
    
    diff = (rate_w45 - rate_w44) if (rate_w45 is not None and rate_w44 is not None) else None
    share_ret = (w45_ret / w45_total_ret_all) if w45_total_ret_all > 0 else 0
    
    bc_summary.append({
        'bc': bc,
        'am': am_name,
        'am_code': am_code,
        'vol': int(w45_tot),
        'ret': int(w45_ret),
        'rate': round(rate_w45, 6) if rate_w45 is not None else 0,
        'rate_prev': round(rate_w44, 6) if rate_w44 is not None else None,
        'diff': round(diff, 6) if diff is not None else None,
        'share_ret': round(share_ret, 6),
        'total_orders': int(w45_tot),
        'return_orders': int(w45_ret),
        'rate_fd': round(rate_w45, 6) if rate_w45 is not None else 0,
        'share_return': round(share_ret, 6)
    })

bc_summary.sort(key=lambda x: x['rate'], reverse=True)
for i, r in enumerate(bc_summary[:15], 1):
    r['stt'] = i
    w44_s = f"{r['rate_prev']*100:.2f}%" if r['rate_prev'] is not None else "None"
    w45_s = f"{r['rate']*100:.2f}%"
    diff_s = f"{r['diff']*100:+.2f}%p" if r['diff'] is not None else "None"
    print(f"{i:2d}. {r['bc']:32s} ({r['am']:20s}): W44={w44_s:7s} | W45={w45_s:7s} | Δ={diff_s:7s} | Vol={r['vol']:5d} | Ret={r['ret']:4d}")

# Save results for inspection
with open('scratch/fd_calculated_results.json', 'w', encoding='utf-8') as f:
    json.dump({'am': am_summary, 'top_bc': bc_summary}, f, ensure_ascii=False, indent=2)
print("\nSaved to scratch/fd_calculated_results.json")
