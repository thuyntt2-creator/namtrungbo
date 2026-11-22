import subprocess, time, json, urllib.request, websocket

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
p = subprocess.Popen([edge_path, '--headless', '--disable-gpu', '--remote-debugging-port=9222', '--remote-allow-origins=*', 'about:blank'])
time.sleep(2)

try:
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    ws_url = [t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page'][0]
    ws = websocket.create_connection(ws_url)
    
    ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
    ws.send(json.dumps({'id': 2, 'method': 'Runtime.enable'}))
    ws.send(json.dumps({'id': 3, 'method': 'Log.enable'}))

    ws.send(json.dumps({'id': 4, 'method': 'Page.navigate', 'params': {'url': 'http://127.0.0.1:3000/hop'}}))

    start = time.time()
    while time.time() - start < 5:
        try:
            ws.settimeout(1.0)
            msg = json.loads(ws.recv())
            if msg.get('method') == 'Runtime.exceptionThrown':
                print('EXCEPTION THROWN:')
                print(json.dumps(msg['params'], indent=2, ensure_ascii=False))
            elif msg.get('method') == 'Runtime.consoleAPICalled':
                print('CONSOLE:', msg['params']['type'], [a.get('value') for a in msg['params']['args']])
        except Exception:
            pass
finally:
    p.kill()

