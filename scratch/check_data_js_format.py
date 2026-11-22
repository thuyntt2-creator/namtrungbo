with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    prefix = f.read(50)
    print("data.js starts with:", prefix)
    f.seek(0, 2)
    print("data.js size:", f.tell())

