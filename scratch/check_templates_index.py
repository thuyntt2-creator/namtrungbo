with open(r'C:\Users\lap4all\Desktop\New folder\templates\index.html', 'r', encoding='utf-8') as f:
    t = f.read()

for s in ['12/10', '16/09', 'W42 (12/10', 'Tuần N (', 'Tuần N-1']:
    print(s, 'count in templates/index.html:', t.count(s))

