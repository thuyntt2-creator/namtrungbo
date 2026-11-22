with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('"fd":')
idx2 = js.find('"am": [', idx)
print(js[idx2:idx2+2500])

