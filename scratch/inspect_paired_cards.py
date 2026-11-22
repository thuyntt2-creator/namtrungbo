with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('const pairedCards = [')
print(js[idx:idx+3500])

