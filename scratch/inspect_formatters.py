with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
matches = [m.start() for m in re.finditer(r'function fPct|function renderDeltaBadge|function fNum', js)]
for m in matches:
    print('--- MATCH AT', m, '---')
    print(js[m:m+500])

