import json, time, subprocess, urllib.request, os

edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]
edge_path = next(p for p in edge_paths if os.path.exists(p))

port = 9333
proc = subprocess.Popen([
    edge_path,
    f"--remote-debugging-port={port}",
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--window-size=1600,1200",
    "http://127.0.0.1:3000/hop"
])

time.sleep(3)

try:
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode())
    target = next(t for t in tabs if "hop" in t.get("url", "") or t.get("type") == "page")
    ws_url = target["webSocketDebuggerUrl"]

    import websocket
    ws = websocket.create_connection(ws_url, timeout=15)

    msg_id = 0
    def send_cmd(method, params=None):
        global msg_id
        msg_id += 1
        msg = {"id": msg_id, "method": method, "params": params or {}}
        ws.send(json.dumps(msg))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == msg_id:
                return resp.get("result", {})

    send_cmd("Runtime.enable")
    time.sleep(2)

    # 1. Check duplicate bullets under hero
    r1 = send_cmd("Runtime.evaluate", {
        "expression": "document.getElementById('banner-overview-bullets') !== null"
    })
    has_dup_bullets = r1.get("result", {}).get("value")
    print("Has duplicate banner bullets:", has_dup_bullets)

    # 2. Check insights count in Key Takeaways
    r2 = send_cmd("Runtime.evaluate", {
        "expression": "document.querySelectorAll('#overview-insights-container .insight-item').length"
    })
    insights_cnt = r2.get("result", {}).get("value")
    print("Insights count in container:", insights_cnt)

    # 3. Check KPI cards decimals
    r3 = send_cmd("Runtime.evaluate", {
        "expression": "Array.from(document.querySelectorAll('#overview-kpi-tiles .kpi-tile')).map(el => ({ title: el.querySelector('.kpi-tile-header')?.innerText, val: el.querySelector('.kpi-tile-value')?.innerText, meta: el.querySelector('.kpi-tile-meta')?.innerText }))"
    })
    tiles = r3.get("result", {}).get("value", [])
    print(f"Verified {len(tiles)} KPI tiles:")
    for t in tiles:
        print("  ", t)

    # 4. Check FD chart
    r4 = send_cmd("Runtime.evaluate", {
        "expression": "(() => { const c = Chart.getChart('chart-fd-bar'); if (!c) return 'No chart'; return { labels: c.data.labels, prevData: c.data.datasets[1].data, currData: c.data.datasets[2].data, diffData: c.data.datasets[3].data }; })()"
    })
    fd_chart_info = r4.get("result", {}).get("value")
    if isinstance(fd_chart_info, dict):
        print("FD Chart labels (count):", len(fd_chart_info["labels"]))
        print("Top 5 AM labels:", fd_chart_info["labels"][:5])
        if "Trần Nguyễn Huyền Trang" in fd_chart_info["labels"]:
            idx = fd_chart_info["labels"].index("Trần Nguyễn Huyền Trang")
            print(f"Trang -> W44: {fd_chart_info['prevData'][idx]}, W45: {fd_chart_info['currData'][idx]}, Diff: {fd_chart_info['diffData'][idx]}")
        if "Nguyễn Ngọc Khánh" in fd_chart_info["labels"]:
            idx = fd_chart_info["labels"].index("Nguyễn Ngọc Khánh")
            print(f"Khanh -> W44: {fd_chart_info['prevData'][idx]}, W45: {fd_chart_info['currData'][idx]}, Diff: {fd_chart_info['diffData'][idx]}")

    # 5. Switch to Tab 13 (COD) and check headers & tiles
    send_cmd("Runtime.evaluate", {
        "expression": "(() => { switchTab('tab-control'); renderControlTab(); return true; })()"
    })
    time.sleep(1)

    r5 = send_cmd("Runtime.evaluate", {
        "expression": "(() => { return { banner: document.getElementById('cod-banner-title')?.innerText, desc: document.getElementById('cod-summary-banner-desc')?.innerText.trim(), totalVal: document.getElementById('kpi-cod-total-val')?.innerText, totalMeta: document.getElementById('kpi-cod-total-meta')?.innerText, thPrev: document.getElementById('th-cod-prev')?.innerText, thCurr: document.getElementById('th-cod-curr')?.innerText }; })()"
    })
    cod_info = r5.get("result", {}).get("value")
    print("COD Tab Info:")
    for k, v in (cod_info or {}).items():
        print(f"  {k}: {v}")

    # Check COD chart labels
    r6 = send_cmd("Runtime.evaluate", {
        "expression": "(() => { const c = Chart.getChart('chart-cod-tm-am-bar'); return c ? c.data.labels : 'No chart'; })()"
    })
    print("COD Chart labels:", r6.get("result", {}).get("value"))

    # Capture screenshots
    import base64
    shot = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_cod_tab_verified.png", "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    print("Saved screenshot_cod_tab_verified.png")

    send_cmd("Runtime.evaluate", {"expression": "switchTab('tab-overview')"})
    time.sleep(1)
    shot2 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_overview_verified.png", "wb") as f:
        f.write(base64.b64decode(shot2["data"]))
    print("Saved screenshot_overview_verified.png")

    send_cmd("Runtime.evaluate", {"expression": "(() => { switchTab('tab-fd'); renderFdTab(); renderFdChart(); })()"})
    time.sleep(1)
    shot3 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_fd_tab_verified.png", "wb") as f:
        f.write(base64.b64decode(shot3["data"]))
    print("Saved screenshot_fd_tab_verified.png")

    ws.close()
finally:
    proc.kill()
