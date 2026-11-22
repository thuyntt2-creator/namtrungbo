with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('Trần Nguyễn Huyền Trang')
print(js[idx-50:idx+400])

