import os

root = r'C:\Users\lap4all\Desktop\New folder'
for fn in ['index.html', 'templates/index.html', 'app.js', 'data.json', 'data.js']:
    p = os.path.join(root, fn)
    if not os.path.exists(p):
        continue
    txt = open(p, 'r', encoding='utf-8', errors='ignore').read()
    for s in ['16/09', '01/08', 'W42 (12/10', 'Tuần N-1', 'Tuần N']:
        c = txt.count(s)
        if c > 0:
            print(f'{fn}: found {c} occurrences of "{s}"')

