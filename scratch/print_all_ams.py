import json

with open('scratch/fd_calculated_results.json', encoding='utf-8') as f:
    res = json.load(f)

print(f"Total AMs: {len(res['am'])}")
for r in res['am']:
    w44_s = f"{r['rate_full_prev']*100:.2f}%" if r['rate_full_prev'] is not None else "None"
    w45_s = f"{r['rate_full']*100:.2f}%" if r['rate_full'] is not None else "None"
    diff_s = f"{r['diff_full']*100:+.2f}%p" if r['diff_full'] is not None else "None"
    print(f"{r['stt']:2d}. {r['am_name']:25s} ({r['am']:10s}): W44={w44_s:7s} | W45={w45_s:7s} | Δ={diff_s:7s} | Vol={r['vol_full']}")
