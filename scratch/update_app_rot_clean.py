with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

# 1. Update tblBodyAM formatting for nulls
old_tbl_am = """      let listAM = [...D.rot_lc.am].map(r => {
        const wPrev = r[prevKey] !== undefined ? (r[prevKey] || 0) : (r.w37 !== undefined ? r.w37 : (r.w36 || 0));
        const wCurr = r[currKey] !== undefined ? (r[currKey] || 0) : (r.w38 !== undefined ? r.w38 : (r.w37 || 0));
        const diff_val = r.diff !== undefined ? r.diff : (wCurr - wPrev);
        const vol_rot = Math.round((r.vol || 0) * wCurr);
        const rate_rot = totalRotAM > 0 ? (vol_rot / totalRotAM) : 0;
        return {
          ...r,
          wPrev,
          wCurr,
          diff_val,
          vol_rot,
          rate_rot
        };
      }).sort((a, b) => (b.vol_rot || 0) - (a.vol_rot || 0) || (b.wCurr || 0) - (a.wCurr || 0));

      tblBodyAM.innerHTML = listAM.map((row, i) => {
        const isSelected = state.selectedAM === row.am;
        const rowClass = isSelected ? 'presenter-laser-box' : '';
        const heatCurr = getHeatmapClass(row.wCurr, 'rot_lc');
        const diffBadge = renderDeltaBadge(row.diff_val, false, true);
        let evalBadge = '<span class="badge-tag badge-tag-green">🟢 Tốt (≤1%)</span>';
        if ((row.wCurr || 0) > 0.05) evalBadge = '<span class="badge-tag badge-tag-red">🔴 Nghiêm Trọng (&gt;5%)</span>';
        else if ((row.wCurr || 0) > 0.02) evalBadge = '<span class="badge-tag badge-tag-amber">🟡 Cảnh Báo (2-5%)</span>';

        return `
          <tr data-entity="${row.am}" class="${rowClass}" style="cursor: pointer;" onclick="selectAndHighlightAM('${row.am}')">
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold" style="font-size:13px; font-weight:800; color:${isSelected ? '#ef4444' : 'inherit'};">${row.am}</td>
            <td class="num">${fNum(row.vol)}</td>
            <td class="num bold" style="background: rgba(239, 68, 68, 0.08); color: ${row.vol_rot > 10 ? '#b91c1c' : 'inherit'}; font-weight: 800; font-size: 13.5px;">${fNum(row.vol_rot)}</td>
            <td class="num bold" style="background: var(--color-amber-bg); color: #ea580c; font-weight: 800; font-size: 13px;">${fPct(row.rate_rot, 1)}</td>
            <td class="num">${fPct(row.wPrev, 2)}</td>
            <td class="num bold ${heatCurr}">${fPct(row.wCurr, 2)}</td>
            <td class="num bold">${diffBadge}</td>
            <td class="center">${evalBadge}</td>
          </tr>
        `;
      }).join('');"""

new_tbl_am = """      let listAM = [...D.rot_lc.am].map(r => {
        const wPrev = (r[prevKey] !== undefined && r[prevKey] !== null) ? r[prevKey] : null;
        const wCurr = (r[currKey] !== undefined && r[currKey] !== null) ? r[currKey] : null;
        const diff_val = (r.diff !== undefined && r.diff !== null) ? r.diff : (wPrev !== null && wCurr !== null ? wCurr - wPrev : null);
        const vol_rot = Math.round((r.vol || 0) * (wCurr || 0));
        const rate_rot = totalRotAM > 0 ? (vol_rot / totalRotAM) : 0;
        return {
          ...r,
          wPrev,
          wCurr,
          diff_val,
          vol_rot,
          rate_rot
        };
      }).sort((a, b) => (b.vol_rot || 0) - (a.vol_rot || 0) || (b.wCurr || 0) - (a.wCurr || 0));

      tblBodyAM.innerHTML = listAM.map((row, i) => {
        const isSelected = state.selectedAM === row.am;
        const rowClass = isSelected ? 'presenter-laser-box' : '';
        const heatCurr = row.wCurr !== null ? getHeatmapClass(row.wCurr, 'rot_lc') : '';
        const diffBadge = (row.diff_val !== null && row.diff_val !== undefined) ? renderDeltaBadge(row.diff_val, false, true) : '<span style="color:var(--text-muted); font-size:12px;">---</span>';
        let evalBadge = '<span class="badge-tag badge-tag-green">🟢 Tốt (≤1%)</span>';
        if (row.wCurr === null) evalBadge = '<span class="badge-tag badge-tag-gray">Chưa Có Data</span>';
        else if ((row.wCurr || 0) > 0.05) evalBadge = '<span class="badge-tag badge-tag-red">🔴 Nghiêm Trọng (&gt;5%)</span>';
        else if ((row.wCurr || 0) > 0.02) evalBadge = '<span class="badge-tag badge-tag-amber">🟡 Cảnh Báo (2-5%)</span>';

        return `
          <tr data-entity="${row.am}" class="${rowClass}" style="cursor: pointer;" onclick="selectAndHighlightAM('${row.am}')">
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold" style="font-size:13px; font-weight:800; color:${isSelected ? '#ef4444' : 'inherit'};">${row.am}</td>
            <td class="num">${fNum(row.vol)}</td>
            <td class="num bold" style="background: rgba(239, 68, 68, 0.08); color: ${row.vol_rot > 10 ? '#b91c1c' : 'inherit'}; font-weight: 800; font-size: 13.5px;">${fNum(row.vol_rot)}</td>
            <td class="num bold" style="background: var(--color-amber-bg); color: #ea580c; font-weight: 800; font-size: 13px;">${fPct(row.rate_rot, 1)}</td>
            <td class="num">${row.wPrev !== null ? fPct(row.wPrev, 2) : '---'}</td>
            <td class="num bold ${heatCurr}">${row.wCurr !== null ? fPct(row.wCurr, 2) : '---'}</td>
            <td class="num bold">${diffBadge}</td>
            <td class="center">${evalBadge}</td>
          </tr>
        `;
      }).join('');"""

if old_tbl_am in app_js:
    app_js = app_js.replace(old_tbl_am, new_tbl_am, 1)
    print("Replaced tblBodyAM in app.js cleanly.")
else:
    print("Warning: old_tbl_am not found in app.js")

# 2. Update renderRotLcBarChart in app.js for null handling and spanGaps
old_chart_map = """      const selectedAM = state.selectedAM;
      const sorted = [...D.rot_lc.am].map(r => {
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

new_chart_map = """      const selectedAM = state.selectedAM;
      const sorted = [...D.rot_lc.am].map(r => {
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

if old_chart_map in app_js:
    app_js = app_js.replace(old_chart_map, new_chart_map, 1)
    print("Replaced chart sorted map in app.js cleanly.")
else:
    print("Warning: old_chart_map not found in app.js")

# Add spanGaps: true to line dataset in rotLcBar
if "label: 'Đường Biến Động WoW (Δ %p)'," in app_js:
    app_js = app_js.replace("label: 'Đường Biến Động WoW (Δ %p)',", "label: 'Đường Biến Động WoW (Δ %p)',\n              spanGaps: true,", 1)
    print("Added spanGaps: true to rotLcBar line chart.")

with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'w', encoding='utf-8') as f:
    f.write(app_js)
print("Saved app.js successfully!")

