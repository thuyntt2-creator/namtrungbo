import json

try:
    with open(r'C:\Users\lap4all\Desktop\New folder\data.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    print("data.json parsed cleanly! Keys:", list(d.keys()))
except Exception as e:
    print("data.json error:", e)

