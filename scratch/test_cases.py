import sys
sys.stdout.reconfigure(encoding='utf-8')

# Test formula for Trường Xuân:
# %GTC 7D: 47.55%
# GTC Best: 65.75% -> target_pct: max(0.50, 0.7 * 0.6575) = max(0.50, 0.46025) = 0.50
# GTC 7D Col O: 263
# total_vol_7d = (263 * 7) / 0.4755 = 3871.71
# vol_6d = 3871.71 * (6/7) = 3318.61
# gtc_6d = (263 * 7) * (6/7) = 263 * 6 = 1578.0

gtc_7d_val = 0.4755
gtc_best = 0.6575
target_pct = max(0.50, 0.7 * gtc_best)
vol_gtc_7d = 263

total_vol_7d = (vol_gtc_7d * 7) / gtc_7d_val
vol_6d = total_vol_7d * (6 / 7)
gtc_6d = (vol_gtc_7d * 7) * (6 / 7)

print(f"Trường Xuân: vol_6d={vol_6d:.1f}, gtc_6d={gtc_6d:.1f}")

# Case A: vol_today = 649 (from auto_chot_so_hang_ve)
vol_today_A = 649
req_A = round(target_pct * (vol_6d + vol_today_A) - gtc_6d)
pct_A = round(req_A / vol_today_A * 100)
print(f"Case A (Vol {vol_today_A}): Target = {req_A} ({pct_A}%)")

# Case B: vol_today = 554 (from alert_targets.json on VPS at 9h)
vol_today_B = 554
req_B = round(target_pct * (vol_6d + vol_today_B) - gtc_6d)
pct_B = round(req_B / vol_today_B * 100)
print(f"Case B (Vol {vol_today_B}): Target = {req_B} ({pct_B}%)")

print("\n--- QUẢNG KHÊ ---")
# %GTC 7D: 47.56%
# GTC Best: 62.78% -> target_pct: 0.50
# GTC 7D Col O: 205
gtc_7d_qk = 0.4756
gtc_best_qk = 0.6278
target_pct_qk = max(0.50, 0.7 * gtc_best_qk)
vol_gtc_7d_qk = 205

total_vol_7d_qk = (vol_gtc_7d_qk * 7) / gtc_7d_qk
vol_6d_qk = total_vol_7d_qk * (6 / 7)
gtc_6d_qk = (vol_gtc_7d_qk * 7) * (6 / 7)
print(f"Quảng Khê: vol_6d={vol_6d_qk:.1f}, gtc_6d={gtc_6d_qk:.1f}")

# Case A: vol_today = 405
vol_today_qk_A = 405
req_qk_A = round(target_pct_qk * (vol_6d_qk + vol_today_qk_A) - gtc_6d_qk)
pct_qk_A = round(req_qk_A / vol_today_qk_A * 100)
print(f"Case A (Vol {vol_today_qk_A}): Target = {req_qk_A} ({pct_qk_A}%)")

# Case B: vol_today = 331
vol_today_qk_B = 331
req_qk_B = round(target_pct_qk * (vol_6d_qk + vol_today_qk_B) - gtc_6d_qk)
pct_qk_B = round(req_qk_B / vol_today_qk_B * 100)
print(f"Case B (Vol {vol_today_qk_B}): Target = {req_qk_B} ({pct_qk_B}%)")
