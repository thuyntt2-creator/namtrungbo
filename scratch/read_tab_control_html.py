with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('id="tab-control"')
print(html[idx:idx+3500])

