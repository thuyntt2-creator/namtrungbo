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
    "about:blank"
])

time.sleep(2)

try:
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode())
    target = tabs[0]
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

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    send_cmd("Log.enable")

    # Navigate to http://127.0.0.1:3000/hop
    send_cmd("Page.navigate", {"url": "http://127.0.0.1:3000/hop"})

    # Collect messages for 5 seconds
    start = time.time()
    errors = []
    while time.time() - start < 5:
        try:
            ws.settimeout(1.0)
            msg = json.loads(ws.recv())
            if msg.get("method") == "Runtime.exceptionThrown":
                errors.append(msg["params"]["exceptionDetails"])
            elif msg.get("method") == "Log.entryAdded":
                if msg["params"]["entry"]["level"] in ["error", "warning"]:
                    print("Log:", msg["params"]["entry"])
        except Exception:
            pass

    print("Uncaught Exceptions:", len(errors))
    for e in errors:
        print("  Exception:", e.get("text"), e.get("exception", {}).get("description"))

    ws.close()
finally:
    proc.kill()

