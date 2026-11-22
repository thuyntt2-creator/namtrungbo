import re, time

root = r'C:\Users\lap4all\Desktop\New folder'

# 1. Update index.html
index_path = f"{root}\\index.html"
with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Update Day table header: W42 -> W44
old_day_th = '<th class="num">Đơn Ngày</th>\n<th class="num">W42</th>'
new_day_th = '<th class="num">Đơn Ngày</th>\n<th class="num">W44</th>'
if old_day_th in html:
    html = html.replace(old_day_th, new_day_th, 1)
    print("Updated Day table header W42 -> W44")
else:
    print("Warning: old_day_th not matched")

# Update Night table header & title: remove W42 and Biến Động (Δ)
old_night_table = """<!-- Bảng 2: OPR Ca Đêm -->
<div class="report-card">
<div class="report-card-header">
<div class="report-card-title">
<i data-lucide="moon" style="color: var(--color-purple);"></i>
              BẢNG 2: %OPR CA ĐÊM (19H–9H - SORT BIẾN ĐỘNG Δ)
            </div>
<span class="badge-tag badge-tag-purple">Ca Đêm (KPI ≥ 80%)</span>
</div>
<div class="report-card-body">
<div class="bi-table-wrap">
<table class="bi-table" id="table-opr-night-detailed">
<thead>
<tr>
<th class="center" style="width: 44px;">#</th>
<th>AM Phụ Trách</th>
<th class="num">Đơn Đêm</th>
<th class="num">W42</th>
<th class="num" style="background: var(--color-amber-bg); font-weight:800; color:#ea580c;">%OPR W45</th>
<th class="num">Biến Động (Δ)</th>
<th class="center">Đánh Giá SLA</th>
</tr>
</thead>
<tbody></tbody>
</table>
</div>
</div>
</div>"""

new_night_table = """<!-- Bảng 2: OPR Ca Đêm -->
<div class="report-card">
<div class="report-card-header">
<div class="report-card-title">
<i data-lucide="moon" style="color: var(--color-purple);"></i>
              BẢNG 2: %OPR CA ĐÊM (19H–9H - XẾP HẠNG THEO %OPR W45)
            </div>
<span class="badge-tag badge-tag-purple">Ca Đêm (KPI ≥ 80%)</span>
</div>
<div class="report-card-body">
<div class="bi-table-wrap">
<table class="bi-table" id="table-opr-night-detailed">
<thead>
<tr>
<th class="center" style="width: 44px;">#</th>
<th>AM Phụ Trách</th>
<th class="num">Đơn Đêm</th>
<th class="num" style="background: var(--color-amber-bg); font-weight:800; color:#ea580c;">%OPR W45</th>
<th class="center">Đánh Giá SLA</th>
</tr>
</thead>
<tbody></tbody>
</table>
</div>
</div>
</div>"""

# Normalize whitespace for matching
def normalize(s):
    return re.sub(r'\s+', ' ', s).strip()

if old_night_table in html:
    html = html.replace(old_night_table, new_night_table, 1)
    print("Replaced Night table HTML cleanly.")
else:
    # Try regex match
    pattern = r'<!-- Bảng 2: OPR Ca Đêm -->[\s\S]*?<table class="bi-table" id="table-opr-night-detailed">[\s\S]*?</table>\s*</div>\s*</div>\s*</div>'
    match = re.search(pattern, html)
    if match:
        html = html[:match.start()] + new_night_table + html[match.end():]
        print("Replaced Night table HTML via regex.")
    else:
        print("ERROR: Night table pattern not matched!")

ts = int(time.time())
html = re.sub(r'data\.js\?v=\d+', f'data.js?v={ts}', html)
html = re.sub(r'app\.js\?v=\d+', f'app.js?v={ts}', html)
html = re.sub(r'styles\.css\?v=\d+', f'styles.css?v={ts}', html)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved index.html")

# 2. Update app.js
app_path = f"{root}\\app.js"
with open(app_path, 'r', encoding='utf-8') as f:
    app_js = f.read()

# Replace tblBodyNight render block
target_night_js = """    // 2. BẢNG 2: %OPR CA ĐÊM (19H-9H)
    const tblBodyNight = document.querySelector('#table-opr-night-detailed tbody');
    if (tblBodyNight) {
      let listNight = [...D.opr_tts.am].map(r => {
        const curr = getNightVal(r);
        const prev = getPrevNightVal(r);
        return {
          ...r,
          curr_val: curr,
          prev_val: prev,
          diff_val: r.diff_night !== undefined ? r.diff_night : ((curr || 0) - (prev || 0))
        };
      }).sort((a, b) => (b.curr_val || 0) - (a.curr_val || 0));

      tblBodyNight.innerHTML = listNight.map((row, i) => {
        const isSelected = state.selectedAM === row.am;
        const rowClass = isSelected ? 'presenter-laser-box' : '';
        const heatW = getHeatmapClass(row.curr_val, 'opr');
        const diffBadge = renderDeltaBadge(row.diff_val, true, true);
        const evalBadge = getOprNightBadge(row.curr_val);

        return `
          <tr data-entity="${row.am}" class="${rowClass}" style="cursor: pointer;" onclick="selectAndHighlightAM('${row.am}')">
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold" style="font-size:13px; font-weight:800; color:${isSelected ? '#ef4444' : 'inherit'};">${row.am}</td>
            <td class="num">${fNum(row.vol_night)}</td>
            <td class="num">${fPct(row.prev_val)}</td>
            <td class="num bold ${heatW}">${fPct(row.curr_val)}</td>
            <td class="num bold">${diffBadge}</td>
            <td class="center">${evalBadge}</td>
          </tr>
        `;
      }).join('');
    }"""

replacement_night_js = """    // 2. BẢNG 2: %OPR CA ĐÊM (19H-9H) — Bỏ so sánh W42/Δ theo yêu cầu
    const tblBodyNight = document.querySelector('#table-opr-night-detailed tbody');
    if (tblBodyNight) {
      let listNight = [...D.opr_tts.am].map(r => {
        const curr = getNightVal(r);
        return {
          ...r,
          curr_val: curr
        };
      }).sort((a, b) => (b.curr_val || 0) - (a.curr_val || 0));

      tblBodyNight.innerHTML = listNight.map((row, i) => {
        const isSelected = state.selectedAM === row.am;
        const rowClass = isSelected ? 'presenter-laser-box' : '';
        const heatW = getHeatmapClass(row.curr_val, 'opr');
        const evalBadge = getOprNightBadge(row.curr_val);

        return `
          <tr data-entity="${row.am}" class="${rowClass}" style="cursor: pointer;" onclick="selectAndHighlightAM('${row.am}')">
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold" style="font-size:13px; font-weight:800; color:${isSelected ? '#ef4444' : 'inherit'};">${row.am}</td>
            <td class="num">${fNum(row.vol_night)}</td>
            <td class="num bold ${heatW}">${fPct(row.curr_val)}</td>
            <td class="center">${evalBadge}</td>
          </tr>
        `;
      }).join('');
    }"""

if target_night_js in app_js:
    app_js = app_js.replace(target_night_js, replacement_night_js, 1)
    print("Replaced tblBodyNight in app.js cleanly.")
else:
    print("WARNING: target_night_js not found in app.js, using regex replacement...")
    # regex fallback
    pat = r'// 2\. BẢNG 2: %OPR CA ĐÊM[\s\S]*?tblBodyNight\.innerHTML\s*=\s*listNight\.map[\s\S]*?\}\)\.join\(\'\'\);\s*\}'
    app_js = re.sub(pat, replacement_night_js.strip(), app_js)
    print("Replaced via regex.")

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_js)
print("Saved app.js")

