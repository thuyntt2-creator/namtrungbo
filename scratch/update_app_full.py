import re, os

root = r'C:\Users\lap4all\Desktop\New folder'

# Read app.js
app_js_path = os.path.join(root, 'app.js')
with open(app_js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update pairedCards in app.js
# Update gtcDiff, odrDiff, ltcDiff, etc to use .replace('.', ',')
js = js.replace("(Math.abs(gtcDiff)*100).toFixed(1)}%p", "(Math.abs(gtcDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(gtcTtsDiff)*100).toFixed(1)}%p", "(Math.abs(gtcTtsDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("Target ≥ 76.0%", "Target ≥ 76,0%")
js = js.replace("(Math.abs(ganDiff)*100).toFixed(1)}%p", "(Math.abs(ganDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(odrDiff)*100).toFixed(1)}%p", "(Math.abs(odrDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(odrTtsDiff)*100).toFixed(1)}%p", "(Math.abs(odrTtsDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(ltcDiff)*100).toFixed(1)}%p", "(Math.abs(ltcDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(ltcTtsDiff)*100).toFixed(1)}%p", "(Math.abs(ltcTtsDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("Target ≥ 90.0%", "Target ≥ 90,0%")
js = js.replace("(Math.abs(rotDiff)*100).toFixed(2)}%p", "(Math.abs(rotDiff)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(fdDiffFull)*100).toFixed(1)}%p", "(Math.abs(fdDiffFull)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("(Math.abs(fdDiffTts)*100).toFixed(1)}%p", "(Math.abs(fdDiffTts)*100).toFixed(1).replace('.', ',')}%p")

# In opr_pair
js = js.replace("((D.opr?.overview?.val_w45 || 0.863) * 100).toFixed(1)}%", "((D.opr?.overview?.val_w45 || 0.863) * 100).toFixed(1).replace('.', ',')}%")
js = js.replace("(Math.abs(D.opr?.overview?.diff || 0.04)*100).toFixed(1)}%p", "(Math.abs(D.opr?.overview?.diff || 0.04)*100).toFixed(1).replace('.', ',')}%p")
js = js.replace("((D.opr?.overview?.rate_day || 0.951) * 100).toFixed(1)}%", "((D.opr?.overview?.rate_day || 0.951) * 100).toFixed(1).replace('.', ',')}%")
js = js.replace("((D.opr?.overview?.rate_night || 0.725) * 100).toFixed(1)}%", "((D.opr?.overview?.rate_night || 0.725) * 100).toFixed(1).replace('.', ',')}%")

# In fd_pair badge: ensure -0,3%p
js = js.replace("▼ -0.3%p", "▼ -0,3%p")

# 2. Update renderFdChart in app.js
am_full_map_js = """
    const amMap = {
      'AM Lợi': 'Lê Minh Lợi', 'AM Linh': 'Trương Quang Linh', 'AM Trang': 'Trần Nguyễn Huyền Trang',
      'AM Nhung': 'Trần Thị Nhung', 'AM Phong': 'Lê Hồng Phong', 'AM Long': 'Nguyễn Thanh Long',
      'AM Vũ': 'Nguyễn Lê Nguyên Vũ', 'AM Duy': 'Phan Đình Duy', 'AM Nhi': 'Phan Nguyễn Yến Nhi',
      'AM Chi': 'Huỳnh Thị Kim Chi', 'AM Thư': 'Thái Thị Thanh Thư', 'AM Trường': 'Lê Văn Trường',
      'AM Phi': 'Nguyễn Hoàng Phi', 'AM D.Long': 'Nguyễn Duy Long', 'AM Thơ': 'Nguyễn Thị Tuyết Thơ',
      'AM Nghĩa': 'Nguyễn Đỗ Minh Nghĩa', 'AM Nhựt': 'Lê Thanh Nhựt', 'AM Nga': 'Hồng Bích Nga',
      'AM Thủy': 'Cao Thị Thanh Thủy', 'AM Khánh': 'Nguyễn Ngọc Khánh',
      'Lê Thị Kim Chi': 'Huỳnh Thị Kim Chi'
    };
"""

# Let's inspect renderFdChart replacement
fd_chart_func_pat = r'function renderFdChart\(\) \{[\s\S]*?charts\.fdBar = new Chart\(ctx, \{[\s\S]*?options: \{[\s\S]*?\}\s*\}\);\s*\}'

new_fd_chart_func = """function renderFdChart() {
    const ctx = document.getElementById('chart-fd-bar');
    if (!ctx || !D.fd || !D.fd.am) return;
    if (charts.fdBar) charts.fdBar.destroy();

    const mode = state.fdChartMode || 'full';
    const selectedAM = state.selectedAM;
    const currW = state.week || D.meta?.latest_week || 'W45';
    const prevW = D.meta?.prev_week || 'W44';

    const amMap = {
      'AM Lợi': 'Lê Minh Lợi', 'AM Linh': 'Trương Quang Linh', 'AM Trang': 'Trần Nguyễn Huyền Trang',
      'AM Nhung': 'Trần Thị Nhung', 'AM Phong': 'Lê Hồng Phong', 'AM Long': 'Nguyễn Thanh Long',
      'AM Vũ': 'Nguyễn Lê Nguyên Vũ', 'AM Duy': 'Phan Đình Duy', 'AM Nhi': 'Phan Nguyễn Yến Nhi',
      'AM Chi': 'Huỳnh Thị Kim Chi', 'AM Thư': 'Thái Thị Thanh Thư', 'AM Trường': 'Lê Văn Trường',
      'AM Phi': 'Nguyễn Hoàng Phi', 'AM D.Long': 'Nguyễn Duy Long', 'AM Thơ': 'Nguyễn Thị Tuyết Thơ',
      'AM Nghĩa': 'Nguyễn Đỗ Minh Nghĩa', 'AM Nhựt': 'Lê Thanh Nhựt', 'AM Nga': 'Hồng Bích Nga',
      'AM Thủy': 'Cao Thị Thanh Thủy', 'AM Khánh': 'Nguyễn Ngọc Khánh',
      'Lê Thị Kim Chi': 'Huỳnh Thị Kim Chi'
    };

    let sorted = [...D.fd.am].map(r => {
      let name = amMap[r.am] || r.am;
      return { ...r, am: name };
    }).sort((a, b) => mode === "tts" ? (b.rate_tts || 0) - (a.rate_tts || 0) : (b.rate_full || 0) - (a.rate_full || 0));

    const labels = sorted.map(d => d.am);
    const rateData = sorted.map(d => {
      const v = mode === 'tts' ? d.rate_tts : d.rate_full;
      return (v === null || v === undefined) ? null : Number((v * 100).toFixed(2));
    });
    const volData = sorted.map(d => mode === 'tts' ? d.vol_tts : d.vol_full);
    const prevData = sorted.map(d => {
      const v = mode === 'tts' ? d.rate_tts_prev : d.rate_full_prev;
      return (v === null || v === undefined) ? null : Number((v * 100).toFixed(2));
    });
    const diffData = sorted.map(d => {
      const v = mode === 'tts' ? d.diff_tts : d.diff_full;
      return (v === null || v === undefined) ? null : Number((v * 100).toFixed(2));
    });

    const barColors = rateData.map((val, idx) => {
      if (selectedAM && selectedAM === sorted[idx].am) return '#dc2626';
      if (val === null) return '#94a3b8';
      if (val > 12.0) return '#ef4444';
      if (val > 8.0) return '#f97316';
      if (val > 6.0) return '#eab308';
      return '#3b82f6';
    });

    charts.fdBar = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: mode === 'tts' ? '🌊 Miền Sản Lượng Giao TTS (Đơn)' : '🌊 Miền Sản Lượng Giao Full (Đơn)',
            data: volData,
            fill: true,
            backgroundColor: mode === 'tts' ? 'rgba(234, 88, 12, 0.12)' : 'rgba(59, 130, 246, 0.12)',
            borderColor: mode === 'tts' ? 'rgba(234, 88, 12, 0.4)' : 'rgba(59, 130, 246, 0.4)',
            borderWidth: 1.5,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: mode === 'tts' ? '#ea580c' : '#2563eb',
            yAxisID: 'yVol',
            order: 4
          },
          {
            type: 'bar',
            label: mode === 'tts' ? `%FD TTS ${prevW} (Tuần Trước)` : `%FD Full ${prevW} (Tuần Trước)`,
            data: prevData,
            backgroundColor: '#94a3b8',
            borderRadius: 4,
            yAxisID: 'y',
            order: 3
          },
          {
            type: 'bar',
            label: mode === 'tts' ? `%FD TTS ${currW} (Hiện Tại)` : `%FD Full ${currW} (Hiện Tại)`,
            data: rateData,
            backgroundColor: barColors,
            borderRadius: 4,
            yAxisID: 'y',
            order: 2
          },
          {
            type: 'line',
            label: 'Đường Biến Động WoW (Δ %p)',
            data: diffData,
            borderColor: '#f26522',
            borderWidth: 2.5,
            tension: 0.2,
            spanGaps: false,
            pointBackgroundColor: diffData.map(d => (d === null) ? 'transparent' : (d <= 0 ? '#10b981' : '#ef4444')),
            pointBorderColor: diffData.map(d => (d === null) ? 'transparent' : '#ffffff'),
            pointBorderWidth: 2,
            pointRadius: diffData.map(d => (d === null) ? 0 : 5),
            pointHoverRadius: diffData.map(d => (d === null) ? 0 : 7),
            yAxisID: 'yDiff',
            order: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { 
            position: 'top',
            labels: {
              color: () => document.body.getAttribute('data-theme') === 'dark' ? '#f1f5f9' : '#0f172a',
              font: { weight: '700', size: 11.5, family: "'Plus Jakarta Sans', sans-serif" }
            }
          },
          datalabels: {
            display: (context) => {
              const val = context.dataset.data[context.dataIndex];
              if (val === null || val === undefined) return false;
              return context.datasetIndex === 2 || context.datasetIndex === 3;
            },
            color: (context) => {
              if (context.datasetIndex === 3) {
                const v = context.dataset.data[context.dataIndex];
                return (v !== null && v <= 0) ? '#047857' : '#b91c1c';
              }
              return document.body.getAttribute('data-theme') === 'dark' ? '#f8fafc' : '#0f172a';
            },
            anchor: (context) => context.datasetIndex === 3 ? 'center' : 'end',
            align: (context) => context.datasetIndex === 3 ? 'bottom' : 'top',
            offset: 4,
            font: {
              size: 11,
              weight: '800',
              family: "'JetBrains Mono', monospace"
            },
            formatter: (val, context) => {
              if (val === null || val === undefined) return '';
              const numStr = Number(val).toFixed(2).replace('.', ',');
              if (context.datasetIndex === 3) {
                const s = val > 0 ? '+' : '';
                return `${s}${numStr}%p`;
              }
              return `${numStr}%`;
            }
          },
          tooltip: {
            callbacks: {
              label: (c) => {
                if (c.raw === null || c.raw === undefined) {
                  return ` ${c.dataset.label}: Không có dữ liệu (${prevW})`;
                }
                if (c.dataset.yAxisID === 'yVol') return ` ${c.dataset.label}: ${fNum(c.parsed.y)} đơn`;
                if (c.dataset.yAxisID === 'yDiff') {
                  const s = c.parsed.y > 0 ? '+' : '';
                  return ` ${c.dataset.label}: ${s}${Number(c.parsed.y).toFixed(2).replace('.', ',')}%p`;
                }
                return ` ${c.dataset.label}: ${Number(c.parsed.y).toFixed(2).replace('.', ',')}%`;
              }
            }
          }
        },
        scales: {
          x: {
            ticks: {
              autoSkip: false,
              maxRotation: 45,
              minRotation: 30,
              font: { size: 10.5, weight: '700' }
            },
            grid: { display: false }
          },
          y: {
            position: 'left',
            title: { display: true, text: '% Tỷ Lệ Hoàn Trả (%FD)', font: { size: 11, weight: '700' } },
            ticks: { callback: v => Number(v).toFixed(1).replace('.', ',') + '%' },
            suggestedMax: 16
          },
          yVol: {
            position: 'right',
            grid: { display: false },
            title: { display: true, text: 'Sản Lượng Đơn Giao', font: { size: 11, weight: '700' } },
            ticks: { callback: v => fNum(v) }
          },
          yDiff: {
            position: 'right',
            grid: { display: false },
            title: { display: true, text: 'Biến Động WoW (Δ %p)', font: { size: 11, weight: '700' } },
            ticks: { callback: v => (v > 0 ? '+' : '') + Number(v).toFixed(1).replace('.', ',') + '%p' }
          }
        }
      }
    });
  }"""

if re.search(fd_chart_func_pat, js):
    js = re.sub(fd_chart_func_pat, lambda m: new_fd_chart_func, js)
    print("Replaced renderFdChart successfully.")
else:
    print("WARNING: fd_chart_func_pat not found.")

# 3. Update renderControlTab and renderCodTmAmBar in app.js
control_tab_pat = r'function renderControlTab\(\) \{[\s\S]*?function renderCodTmAmBar\(\) \{[\s\S]*?layout: \{ padding: \{ top: 20, bottom: 8 \} \},'

new_control_tab = """  function renderControlTab() {
    const seg = state.codSegment || 'trend';
    const report = D.cod_report || {};

    const currWStr = state.week || D.meta?.latest_week || 'W45';
    const currWNum = parseInt(currWStr.replace(/\\D/g, ''), 10) || 45;
    const prevWNum = currWNum - 1;
    const prevWStr = `W${prevWNum}`;

    const prevDateRange = getCodIsoWeekRange(prevWNum, 2026);
    const currDateRange = getCodIsoWeekRange(currWNum, 2026);

    const prevPeriod = `Tuần ${prevWStr} (${prevDateRange})`;
    const currPeriod = `Tuần ${currWStr} (${currDateRange})`;

    report.prev_period = prevPeriod;
    report.curr_period = currPeriod;

    const bannerTitle = document.getElementById('cod-banner-title');
    if (bannerTitle) {
      bannerTitle.textContent = `BÁO CÁO COD – SO SÁNH BIẾN ĐỘNG 2 TUẦN (${prevPeriod} vs ${currPeriod}) | VÙNG NTB`;
    }

    const topBad = (report.am_comparison || [])
      .filter(r => parseFloat(r.curr_tm) >= 70)
      .map(r => `${r.am} (${r.curr_tm.replace('.', ',')})`);
    const bannerDescEl = document.getElementById('cod-summary-banner-desc');
    if (bannerDescEl) {
      bannerDescEl.innerHTML = `
        • <strong>${prevPeriod}: 40,0% TM &nbsp;➔&nbsp; ${currPeriod}: 41,3% TM &nbsp;|&nbsp; Biến động: +1,3%p (Xấu đi ⚠️)</strong><br>
        • <strong>Top AM cần giảm tiền mặt gấp (≥70% TM):</strong> ${topBad.length ? topBad.join(', ') : 'Không có'}.
      `;
    }

    const totalMetric = (report.metrics || []).find(m => m.chi_so.includes('Tổng COD'));
    const cashMetric = (report.metrics || []).find(m => m.chi_so.includes('Tiền mặt') && !m.chi_so.includes('Tỷ lệ'));
    const bankMetric = (report.metrics || []).find(m => m.chi_so.includes('Chuyển khoản'));
    const tmRateMetric = (report.metrics || []).find(m => m.chi_so.includes('Tỷ lệ') || m.chi_so.includes('% TM'));

    const badgeEl = document.getElementById('cod-summary-banner-badge');
    if (badgeEl && totalMetric && tmRateMetric) {
      badgeEl.textContent = `Tổng COD: ${totalMetric.curr.replace('.', ',')} Tr | % TM: ${tmRateMetric.curr.replace('.', ',')}`;
    }

    // 4 KPI Tiles
    if (totalMetric) {
      const elVal = document.getElementById('kpi-cod-total-val');
      const elMeta = document.getElementById('kpi-cod-total-meta');
      const elTitle = document.getElementById('kpi-cod-total-title');
      if (elTitle) elTitle.textContent = `Tổng COD Thu Hộ (${currPeriod})`;
      if (elVal) elVal.innerHTML = `${totalMetric.curr.replace('.', ',')} <small>Tr ₫</small>`;
      if (elMeta) elMeta.innerHTML = `<span class="diff-tag diff-neutral">${prevPeriod}: ${totalMetric.prev.replace('.', ',')} Tr ₫ (${totalMetric.diff_pct.replace('.', ',')})</span>`;
    }

    if (cashMetric) {
      const elVal = document.getElementById('kpi-cod-cash-val');
      const elMeta = document.getElementById('kpi-cod-cash-meta');
      const elTitle = document.getElementById('kpi-cod-cash-title');
      if (elTitle) elTitle.textContent = `Tiền Mặt (${currPeriod})`;
      if (elVal) elVal.innerHTML = `${cashMetric.curr.replace('.', ',')} <small>Tr ₫</small>`;
      if (elMeta) elMeta.innerHTML = `<span class="diff-tag diff-neutral">${prevPeriod}: ${cashMetric.prev.replace('.', ',')} Tr ₫ (${cashMetric.diff_pct.replace('.', ',')})</span>`;
    }

    if (bankMetric) {
      const elVal = document.getElementById('kpi-cod-bank-val');
      const elMeta = document.getElementById('kpi-cod-bank-meta');
      const elTitle = document.getElementById('kpi-cod-bank-title');
      if (elTitle) elTitle.textContent = `Chuyển Khoản (${currPeriod})`;
      if (elVal) elVal.innerHTML = `${bankMetric.curr.replace('.', ',')} <small>Tr ₫</small>`;
      if (elMeta) elMeta.innerHTML = `<span class="diff-tag diff-neutral">${prevPeriod}: ${bankMetric.prev.replace('.', ',')} Tr ₫ (${bankMetric.diff_pct.replace('.', ',')})</span>`;
    }

    if (tmRateMetric) {
      const elVal = document.getElementById('kpi-cod-rate-val');
      const elMeta = document.getElementById('kpi-cod-rate-meta');
      const elTitle = document.getElementById('kpi-cod-rate-title');
      if (elTitle) elTitle.textContent = `Tỷ Lệ Tiền Mặt (% TM)`;
      if (elVal) elVal.textContent = `${tmRateMetric.curr.replace('.', ',')}`;
      const isBad = tmRateMetric.diff_val.startsWith('+') || !tmRateMetric.diff_val.startsWith('-');
      if (elMeta) elMeta.innerHTML = `<span class="diff-tag ${isBad ? 'diff-up-bad' : 'diff-down-good'}">${isBad ? '▲ Tăng' : '▼ Giảm'} ${tmRateMetric.diff_val.replace('.', ',')}p (${prevPeriod}: ${tmRateMetric.prev.replace('.', ',')})</span>`;
    }

    // Dynamic Table 1 Header & Title
    const thPrev = document.getElementById('th-cod-prev');
    const thCurr = document.getElementById('th-cod-curr');
    if (thPrev) thPrev.textContent = prevPeriod;
    if (thCurr) thCurr.textContent = currPeriod;
    const cardTitle1 = document.querySelector('#cod-panel-trend .report-card-title');
    if (cardTitle1) {
      cardTitle1.innerHTML = `<i data-lucide="table" style="color: var(--color-blue);"></i> BẢNG ĐỐI CHIẾU CÁC CHỈ SỐ COD CHÍNH (${prevPeriod} vs ${currPeriod})`;
    }

    // Dynamic Table 2 Header & Title
    const cardTitle2 = document.querySelector('#cod-panel-am .report-card-title');
    if (cardTitle2) {
      cardTitle2.innerHTML = `<i data-lucide="users" style="color: var(--color-purple);"></i> BẢNG SO SÁNH TỶ LỆ TIỀN MẶT THEO 20 AM (${prevPeriod} vs ${currPeriod})`;
    }
    const thAmPrev = document.querySelector('#table-cod-am-sheet thead th:nth-child(3)');
    const thAmCurr = document.querySelector('#table-cod-am-sheet thead th:nth-child(4)');
    const thAmLevel = document.querySelector('#table-cod-am-sheet thead th:nth-child(7)');
    if (thAmPrev) thAmPrev.textContent = `Tuần ${prevWStr} (% TM)`;
    if (thAmCurr) thAmCurr.textContent = `Tuần ${currWStr} (% TM)`;
    if (thAmLevel) thAmLevel.textContent = `Mức Độ Tuần ${currWStr}`;

    // Dynamic Table 3 Header & Title
    const cardTitle3 = document.querySelector('#cod-panel-bc .report-card-title');
    if (cardTitle3) {
      cardTitle3.innerHTML = `<i data-lucide="building-2" style="color: var(--ghn-orange);"></i> CHI TIẾT TOÀN BỘ BƯU CỤC – SO SÁNH % TIỀN MẶT ${prevWStr} vs ${currWStr}`;
    }
    const thBcPrev = document.querySelector('#table-cod-bc-sheet thead th:nth-child(4)');
    const thBcCurr = document.querySelector('#table-cod-bc-sheet thead th:nth-child(5)');
    const thBcCash = document.querySelector('#table-cod-bc-sheet thead th:nth-child(7)');
    const thBcLevel = document.querySelector('#table-cod-bc-sheet thead th:nth-child(8)');
    if (thBcPrev) thBcPrev.textContent = `Tuần ${prevWStr} (% TM)`;
    if (thBcCurr) thBcCurr.textContent = `Tuần ${currWStr} (% TM)`;
    if (thBcCash) thBcCash.textContent = `Tiền Mặt ${currWStr} (Tr ₫)`;
    if (thBcLevel) thBcLevel.textContent = `Mức Độ ${currWStr}`;

    // Dynamic Table 4 Header & Title
    const cardTitle4 = document.querySelector('#cod-panel-action .report-card-title');
    if (cardTitle4) {
      cardTitle4.innerHTML = `<i data-lucide="alert-triangle" style="color: var(--color-red);"></i> HƯỚNG XỬ LÝ CÁC AM CÓ TỶ LỆ TIỀN MẶT CAO TRONG TUẦN ${currWStr} (≥ 50%)`;
    }
    const thActionPrev = document.querySelector('#table-cod-action-sheet thead th:nth-child(2)');
    const thActionCurr = document.querySelector('#table-cod-action-sheet thead th:nth-child(3)');
    if (thActionPrev) thActionPrev.textContent = `Tuần ${prevWStr}`;
    if (thActionCurr) thActionCurr.textContent = `Tuần ${currWStr} (% TM)`;

    // 1. PANEL 1: XU HƯỚNG 2 TUẦN
    const tblTrend = document.querySelector('#table-cod-trend-metrics tbody');
    if (tblTrend && report.metrics) {
      tblTrend.innerHTML = report.metrics.map(r => {
        const isTM = r.chi_so.includes('Tiền mặt') || r.chi_so.includes('Tỷ lệ');
        const evalBadge = r.eval.includes('Xấu') 
          ? '<span class="badge-tag badge-tag-red">▲ Xấu (Tăng TM)</span>'
          : (r.eval === '–' ? '<span class="badge-tag badge-tag-blue">—</span>' : `<span class="badge-tag badge-tag-green">${r.eval}</span>`);
        
        const prevFmt = r.prev.replace('.', ',');
        const currFmt = r.curr.replace('.', ',');
        const diffValFmt = r.diff_val.replace('.', ',');
        const diffPctFmt = r.diff_pct.replace('.', ',');

        return `
          <tr style="${isTM ? 'background: rgba(220, 38, 38, 0.04); font-weight: 700;' : ''}">
            <td class="bold" style="font-size:13px; font-weight:800;">${r.chi_so}</td>
            <td class="num">${prevFmt}</td>
            <td class="num bold" style="background: rgba(2, 132, 199, 0.08); color: #0369a1; font-size:13.5px;">${currFmt}</td>
            <td class="num bold" style="color: ${r.diff_val.startsWith('-') ? '#10b981' : '#ef4444'};">${diffValFmt}</td>
            <td class="num bold">${diffPctFmt}</td>
            <td class="center">${evalBadge}</td>
          </tr>
        `;
      }).join('');
    }

    // 2. PANEL 2: AM SO SÁNH 2 TUẦN
    const tblAM = document.querySelector('#table-cod-am-sheet tbody');
    if (tblAM && report.am_comparison) {
      const selectedAM = state.selectedAM;
      tblAM.innerHTML = report.am_comparison.map((r, i) => {
        const isSelected = selectedAM === r.am;
        const rowClass = isSelected ? 'presenter-laser-box' : '';
        const levelBadge = r.level.includes('Nghiêm trọng')
          ? '<span class="badge-tag badge-tag-red">🔴 Nghiêm trọng (≥70%)</span>'
          : (r.level.includes('cải thiện') ? '<span class="badge-tag badge-tag-amber">🟡 Cần cải thiện (50-70%)</span>' : '<span class="badge-tag badge-tag-green">🟢 Tốt (&lt;50%)</span>');
        
        return `
          <tr data-entity="${r.am}" class="${rowClass}" style="cursor: pointer;" onclick="selectAndHighlightAM('${r.am}')">
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold" style="font-size:13px; font-weight:800; color:${isSelected ? '#ef4444' : 'inherit'};">${r.am}</td>
            <td class="num">${r.prev_tm.replace('.', ',')}</td>
            <td class="num bold" style="background: rgba(2, 132, 199, 0.08); color: ${parseFloat(r.curr_tm) >= 70 ? '#dc2626' : (parseFloat(r.curr_tm) >= 50 ? '#d97706' : '#16a34a')}; font-size:13.5px; font-weight:900;">${r.curr_tm.replace('.', ',')}</td>
            <td class="num bold" style="color: ${r.diff.startsWith('+') ? '#dc2626' : (r.diff.startsWith('-') ? '#16a34a' : 'inherit')};">${r.diff.replace('.', ',')}</td>
            <td class="center bold" style="color: ${r.trend.includes('Tăng') ? '#dc2626' : (r.trend.includes('Giảm') ? '#16a34a' : 'inherit')};">${r.trend.replace('.', ',')}</td>
            <td class="center">${levelBadge}</td>
          </tr>
        `;
      }).join('');
    }

    // 3. PANEL 3: CHI TIẾT BƯU CỤC 2 TUẦN
    const tblBC = document.querySelector('#table-cod-bc-sheet tbody');
    if (tblBC && report.bc_details) {
      const selectedAM = state.selectedAM;
      const searchKey = (document.getElementById('search-cod-bc')?.value || '').trim().toLowerCase();

      let bcList = [...report.bc_details];
      if (selectedAM) bcList = bcList.filter(b => b.am === selectedAM);
      if (searchKey) bcList = bcList.filter(b => b.bc.toLowerCase().includes(searchKey) || b.am.toLowerCase().includes(searchKey));

      tblBC.innerHTML = bcList.map((r, i) => {
        const levelBadge = r.level.includes('Nghiêm trọng')
          ? '<span class="badge-tag badge-tag-red">🔴 Nghiêm trọng (≥70%)</span>'
          : (r.level.includes('cải thiện') ? '<span class="badge-tag badge-tag-amber">🟡 Cần cải thiện (50-70%)</span>' : '<span class="badge-tag badge-tag-green">🟢 Tốt (&lt;50%)</span>');
        
        return `
          <tr>
            <td class="center">${renderRankPill(i)}</td>
            <td class="bold">${r.am}</td>
            <td class="bold">${r.bc}</td>
            <td class="num">${r.prev_tm.replace('.', ',')}</td>
            <td class="num bold" style="background: rgba(2, 132, 199, 0.08); color: ${parseFloat(r.curr_tm) >= 70 ? '#dc2626' : (parseFloat(r.curr_tm) >= 50 ? '#d97706' : '#16a34a')};">${r.curr_tm.replace('.', ',')}</td>
            <td class="num bold" style="color: ${r.diff.startsWith('+') ? '#dc2626' : (r.diff.startsWith('-') ? '#16a34a' : 'inherit')};">${r.diff.replace('.', ',')}</td>
            <td class="num">${r.cash_m.replace('.', ',')}</td>
            <td class="center">${levelBadge}</td>
          </tr>
        `;
      }).join('');
    }

    // 4. PANEL 4: HƯỚNG XỬ LÝ AM
    const tblAction = document.querySelector('#table-cod-action-sheet tbody');
    if (tblAction && report.actions) {
      tblAction.innerHTML = report.actions.map(r => {
        const diffNum = parseFloat(r.diff);
        const isBadDiff = !isNaN(diffNum) && diffNum > 0;
        return `
          <tr>
            <td class="bold" style="font-size:13.5px; color:#1e3a8a;">${r.am}</td>
            <td class="num">${r.prev_tm.replace('.', ',')}</td>
            <td class="num bold" style="background: rgba(220, 38, 38, 0.08); color: #dc2626; font-size:13.5px;">${r.curr_tm.replace('.', ',')}</td>
            <td class="num bold" style="color: ${isBadDiff ? '#dc2626' : '#16a34a'};">${r.diff.replace('.', ',')}</td>
            <td style="line-height: 1.6; font-size: 12.5px;">${r.action.replace(/\\n/g, '<br>')}</td>
            <td class="center"><span class="badge-tag ${r.deadline.includes('24h') ? 'badge-tag-red' : 'badge-tag-amber'}">${r.deadline}</span></td>
          </tr>
        `;
      }).join('');
    }

    if (window.lucide) lucide.createIcons();
  }

  function renderCodTmAmBar() {
    const ctx = document.getElementById('chart-cod-tm-am-bar');
    if (!ctx) return;
    if (charts.codTmAmBar) charts.codTmAmBar.destroy();

    const report = D.cod_report || {};
    const currWStr = state.week || D.meta?.latest_week || 'W45';
    const currWNum = parseInt(currWStr.replace(/\\D/g, ''), 10) || 45;
    const prevWNum = currWNum - 1;
    const prevWStr = `W${prevWNum}`;
    const prevDateRange = getCodIsoWeekRange(prevWNum, 2026);
    const currDateRange = getCodIsoWeekRange(currWNum, 2026);

    const prevLabel = `Tuần ${prevWStr} (${prevDateRange})`;
    const currLabel = `Tuần ${currWStr} (${currDateRange})`;

    const cashMetric = (report.metrics || []).find(m => m.chi_so.includes('Tiền mặt') && !m.chi_so.includes('Tỷ lệ'));
    const bankMetric = (report.metrics || []).find(m => m.chi_so.includes('Chuyển khoản'));

    const cashPrev = cashMetric ? parseFloat(cashMetric.prev.replace(/,/g, '')) : 230657.3;
    const cashCurr = cashMetric ? parseFloat(cashMetric.curr.replace(/,/g, '')) : 232553.6;
    const bankPrev = bankMetric ? parseFloat(bankMetric.prev.replace(/,/g, '')) : 345747.4;
    const bankCurr = bankMetric ? parseFloat(bankMetric.curr.replace(/,/g, '')) : 330869.6;

    charts.codTmAmBar = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [prevLabel, currLabel],
        datasets: [
          {
            label: 'Tiền Mặt (Triệu ₫)',
            data: [cashPrev, cashCurr],
            backgroundColor: '#ef4444',
            borderRadius: 4
          },
          {
            label: 'Chuyển Khoản (Triệu ₫)',
            data: [bankPrev, bankCurr],
            backgroundColor: '#10b981',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 20, bottom: 8 } },
        scales: {
          x: { stacked: true },
          y: {
            stacked: true,
            ticks: { callback: v => fNum(v) + ' Tr' },
            title: { display: true, text: 'Tổng Tiền COD (Triệu VNĐ)', font: { weight: '700', size: 11 } }
          }
        },
        plugins: {
          legend: { position: 'top' },
          tooltip: {
            callbacks: {
              label: c => ` ${c.dataset.label}: ${fNum(c.parsed.y)} Triệu VNĐ`
            }
          }
        }
      }
    });
  }
"""

if re.search(control_tab_pat, js):
    js = re.sub(control_tab_pat, lambda m: new_control_tab, js)
    print("Replaced renderControlTab and renderCodTmAmBar successfully.")
else:
    print("WARNING: control_tab_pat not found.")

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("app.js completely updated.")

