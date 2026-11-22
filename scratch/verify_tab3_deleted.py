import subprocess, time, json, urllib.request, base64, sys, tempfile

temp_dir = tempfile.mkdtemp()
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9228
cmd = [
    edge_path,
    '--headless',
    f'--remote-debugging-port={port}',
    f'--user-data-dir={temp_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--window-size=1600,1200',
    'http://127.0.0.1:3000/hop'
]
proc = subprocess.Popen(cmd)
time.sleep(2.5)

try:
    tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json').read())
    import websocket
    ws_url = tabs[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    expr = """
    (function() {
        const tabBtn = document.querySelector('.nav-tab[data-tab="tab-gtc-tong"]');
        if (tabBtn) tabBtn.click();
        return {
            title: document.title,
            tabGtcActive: document.getElementById('tab-gtc-tong') ? document.getElementById('tab-gtc-tong').classList.contains('active') : false,
            hasOldTable: !!document.getElementById('table-bc-canh-bao'),
            hasOldTableOverview: !!document.getElementById('table-bc-canh-bao-overview'),
            hasRealtimeTable: !!document.getElementById('table-bc-baton-ntbo')
        };
    })()
    """
    msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}
    ws.send(json.dumps(msg))
    res = json.loads(ws.recv())
    val = res.get('result', {}).get('result', {}).get('value')
    print('Tab 3 info:', val, flush=True)

    time.sleep(1)

    msg = {'id': 2, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}
    ws.send(json.dumps(msg))
    res = json.loads(ws.recv())
    img_data = base64.b64decode(res['result']['data'])
    screenshot_path = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_tab3_no_old_table.png'
    with open(screenshot_path, 'wb') as f:
        f.write(img_data)
    print('Screenshot saved:', screenshot_path, flush=True)

    ws.close()
finally:
    proc.terminate()
