import subprocess, time, json, urllib.request, websocket, base64

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
p = subprocess.Popen([edge_path, '--headless', '--disable-gpu', '--remote-debugging-port=9222', '--remote-allow-origins=*', 'about:blank'])
time.sleep(2)

try:
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    ws_url = [t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page'][0]
    ws = websocket.create_connection(ws_url)
    
    ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'http://127.0.0.1:3000/hop'}}))
    time.sleep(4)

    # 1. Overview Tab Verification
    script_overview = """
    (() => {
        if (window.switchTab) window.switchTab('tab-overview');
        return {
            has_dup_bullets: document.getElementById('banner-overview-bullets') !== null,
            insights_count: document.querySelectorAll('#overview-insights-container .insight-item').length,
            insights: Array.from(document.querySelectorAll('#overview-insights-container .insight-item')).map(el => ({
                title: el.querySelector('.insight-title')?.innerText,
                desc: el.querySelector('.insight-desc')?.innerText
            })),
            kpi_tiles: Array.from(document.querySelectorAll('#overview-kpi-tiles .kpi-tile')).map(el => ({
                title: el.querySelector('.kpi-tile-header span')?.innerText,
                val: el.querySelector('.kpi-tile-value')?.innerText.trim(),
                meta: el.querySelector('.kpi-tile-meta')?.innerText.trim()
            })),
            vol_chart_summary: document.querySelector('.grid-row-2 .report-card .report-card-body')?.innerText.substring(0, 120)
        };
    })()
    """
    ws.send(json.dumps({'id': 101, 'method': 'Runtime.evaluate', 'params': {'expression': script_overview, 'returnByValue': True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 101:
            print('=== 1. OVERVIEW TAB RESULT ===')
            print(json.dumps(m['result']['result']['value'], indent=2, ensure_ascii=False))
            break

    # Screenshot Overview
    ws.send(json.dumps({'id': 102, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 102:
            with open(r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_overview_w45.png', 'wb') as f:
                f.write(base64.b64decode(m['result']['data']))
            print("Saved screenshot_overview_w45.png")
            break

    # 2. FD Tab Verification
    script_fd = """
    (() => {
        if (window.switchTab) {
            window.switchTab('tab-fd');
            if (window.renderFdTab) window.renderFdTab();
            if (window.renderFdChart) window.renderFdChart();
        }
        const c = window.Chart && Chart.getChart('chart-fd-bar');
        return {
            chart_exists: c !== null,
            chart_labels_count: c ? c.data.labels.length : 0,
            chart_labels: c ? c.data.labels : [],
            datasets: c ? c.data.datasets.map(d => ({ label: d.label, type: d.type, sampleData: d.data.slice(0, 5) })) : [],
            trang_prev: c ? c.data.datasets[1].data[c.data.labels.indexOf('Trần Nguyễn Huyền Trang')] : 'N/A',
            trang_curr: c ? c.data.datasets[2].data[c.data.labels.indexOf('Trần Nguyễn Huyền Trang')] : 'N/A',
            trang_diff: c ? c.data.datasets[3].data[c.data.labels.indexOf('Trần Nguyễn Huyền Trang')] : 'N/A',
            khanh_prev: c ? c.data.datasets[1].data[c.data.labels.indexOf('Nguyễn Ngọc Khánh')] : 'N/A',
            khanh_curr: c ? c.data.datasets[2].data[c.data.labels.indexOf('Nguyễn Ngọc Khánh')] : 'N/A',
            khanh_diff: c ? c.data.datasets[3].data[c.data.labels.indexOf('Nguyễn Ngọc Khánh')] : 'N/A'
        };
    })()
    """
    ws.send(json.dumps({'id': 201, 'method': 'Runtime.evaluate', 'params': {'expression': script_fd, 'returnByValue': True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 201:
            print('=== 2. FD TAB RESULT ===')
            print(json.dumps(m['result']['result']['value'], indent=2, ensure_ascii=False))
            break

    # Screenshot FD
    ws.send(json.dumps({'id': 202, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 202:
            with open(r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_fd_w45.png', 'wb') as f:
                f.write(base64.b64decode(m['result']['data']))
            print("Saved screenshot_fd_w45.png")
            break

    # 3. COD Tab Verification
    script_cod = """
    (() => {
        if (window.switchTab) {
            window.switchTab('tab-control');
            if (window.renderControlTab) window.renderControlTab();
        }
        const c = window.Chart && Chart.getChart('chart-cod-tm-am-bar');
        return {
            banner_title: document.getElementById('cod-banner-title')?.innerText,
            banner_badge: document.getElementById('cod-summary-banner-badge')?.innerText,
            banner_desc: document.getElementById('cod-summary-banner-desc')?.innerText.trim(),
            kpi_total_title: document.getElementById('kpi-cod-total-title')?.innerText,
            kpi_total_val: document.getElementById('kpi-cod-total-val')?.innerText,
            kpi_total_meta: document.getElementById('kpi-cod-total-meta')?.innerText,
            kpi_cash_title: document.getElementById('kpi-cod-cash-title')?.innerText,
            kpi_cash_val: document.getElementById('kpi-cod-cash-val')?.innerText,
            kpi_cash_meta: document.getElementById('kpi-cod-cash-meta')?.innerText,
            kpi_bank_title: document.getElementById('kpi-cod-bank-title')?.innerText,
            kpi_bank_val: document.getElementById('kpi-cod-bank-val')?.innerText,
            kpi_bank_meta: document.getElementById('kpi-cod-bank-meta')?.innerText,
            kpi_rate_title: document.getElementById('kpi-cod-rate-title')?.innerText,
            kpi_rate_val: document.getElementById('kpi-cod-rate-val')?.innerText,
            kpi_rate_meta: document.getElementById('kpi-cod-rate-meta')?.innerText,
            th_prev: document.getElementById('th-cod-prev')?.innerText,
            th_curr: document.getElementById('th-cod-curr')?.innerText,
            card_title1: document.querySelector('#cod-panel-trend .report-card-title')?.innerText.trim(),
            table_row1: Array.from(document.querySelectorAll('#table-cod-trend-metrics tbody tr:nth-child(1) td')).map(td => td.innerText),
            table_row4: Array.from(document.querySelectorAll('#table-cod-trend-metrics tbody tr:nth-child(4) td')).map(td => td.innerText),
            chart_labels: c ? c.data.labels : null
        };
    })()
    """
    ws.send(json.dumps({'id': 301, 'method': 'Runtime.evaluate', 'params': {'expression': script_cod, 'returnByValue': True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 301:
            print('=== 3. COD TAB RESULT ===')
            print(json.dumps(m['result']['result']['value'], indent=2, ensure_ascii=False))
            break

    # Screenshot COD
    ws.send(json.dumps({'id': 302, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == 302:
            with open(r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_cod_w45.png', 'wb') as f:
                f.write(base64.b64decode(m['result']['data']))
            print("Saved screenshot_cod_w45.png")
            break

    ws.close()
finally:
    p.kill()

