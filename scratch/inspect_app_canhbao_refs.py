with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
matches = re.finditer(r'table-bc-canh-bao|renderBcCanhBaoTable', js)
for m in matches:
    idx = m.start()
    print('--- At', idx, '---')
    print(js[max(0, idx-40):min(len(js), idx+150)])

