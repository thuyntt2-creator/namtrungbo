with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-kichban"')
print("Found tab-kichban:", idx != -1)
if idx != -1:
    print(text[idx:idx+400])

