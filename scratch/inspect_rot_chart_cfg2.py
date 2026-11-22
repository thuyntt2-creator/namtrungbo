with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("charts.rotLcBar = new Chart")
print(text[idx+1300:idx+2600])

