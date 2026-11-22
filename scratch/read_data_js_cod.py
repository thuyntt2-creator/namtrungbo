with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('cod_report')
print(js[idx:idx+2500])

