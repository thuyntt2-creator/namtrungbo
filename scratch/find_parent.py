with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-gtc-tong"')
print("=== 500 chars before tab-gtc-tong ===")
print(text[max(0, idx-500):idx])

