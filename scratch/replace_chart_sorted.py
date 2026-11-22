with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

target = """    const sorted = [...D.rot_lc.am].map(r => {
      const prev_val = r[currKey] !== undefined ? (r[prevKey] || 0) : (r.w37 || 0);
      const curr_val = r[currKey] !== undefined ? (r[currKey] || 0) : (r.w38 || 0);
      const diff_val = r.diff !== undefined ? r.diff : (curr_val - prev_val);
      return {
        ...r,
        w34_pct: Number((prev_val * 100).toFixed(2)),
        w35_pct: Number((curr_val * 100).toFixed(2)),
        diff_pct: Number((diff_val * 100).toFixed(2))
      };
    }).sort((a, b) => (b.w35_pct || 0) - (a.w35_pct || 0));"""

replacement = """    const sorted = [...D.rot_lc.am].map(r => {
      const prev_val = (r[prevKey] !== undefined && r[prevKey] !== null) ? r[prevKey] : null;
      const curr_val = (r[currKey] !== undefined && r[currKey] !== null) ? r[currKey] : null;
      const diff_val = (r.diff !== undefined && r.diff !== null) ? r.diff : (prev_val !== null && curr_val !== null ? curr_val - prev_val : null);
      return {
        ...r,
        w34_pct: prev_val !== null ? Number((prev_val * 100).toFixed(2)) : null,
        w35_pct: curr_val !== null ? Number((curr_val * 100).toFixed(2)) : null,
        diff_pct: diff_val !== null ? Number((diff_val * 100).toFixed(2)) : null
      };
    }).sort((a, b) => (b.w35_pct || 0) - (a.w35_pct || 0));"""

assert target in app_js, "Target not found!"
app_js = app_js.replace(target, replacement, 1)

with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'w', encoding='utf-8') as f:
    f.write(app_js)

print("Replaced chart sorted mapping in app.js successfully!")

