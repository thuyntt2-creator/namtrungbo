with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('function renderOverviewTab()')
print(js[idx:idx+1500])

