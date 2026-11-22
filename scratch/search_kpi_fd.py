with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
matches = [m.start() for m in re.finditer(r'kpi-fd|renderFdTab|rate_full', js)]
for m in matches[:10]:
    print('--- MATCH AT', m, '---')
    print(js[max(0, m-50):min(len(js), m+250)])

