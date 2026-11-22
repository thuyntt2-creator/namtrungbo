with open(r'C:\Users\lap4all\Desktop\New folder\app.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("def serve_kichban")
if idx == -1:
    idx = text.find("route('/kich-ban')")
print(text[max(0, idx-100):idx+500])

