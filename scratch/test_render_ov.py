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

    res = send_cmd("Runtime.evaluate", {
        "expression": "(() => { try { renderOverviewTab(); return 'OK'; } catch (e) { return e.stack || e.message; } })()",
        "returnByValue": True
    })
    print("renderOverviewTab execution result:", res.get("result", {}).get("value"))

    res2 = send_cmd("Runtime.evaluate", {
        "expression": "document.getElementById('overview-insights-container')?.innerHTML.length",
        "returnByValue": True
    })
    print("insights innerHTML length:", res2.get("result", {}).get("value"))

    ws.close()
finally:
    proc.kill()

