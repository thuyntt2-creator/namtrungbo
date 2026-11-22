with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

for i, line in enumerate(js.splitlines()):
    if 'renderControlTab' in line or 'tab-control' in line or 'getCodIsoWeekRange' in line:
        print(f'{i+1}: {line}')

