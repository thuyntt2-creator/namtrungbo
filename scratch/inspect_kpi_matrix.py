with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('id="table-overview-kpi-data"')
if idx == -1:
    idx = js.find('table-overview-kpi-data')
print(js[idx:idx+2500])

