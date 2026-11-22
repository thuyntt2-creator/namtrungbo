with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('function renderFdChart()')
print(js[idx+3500:idx+5500])

