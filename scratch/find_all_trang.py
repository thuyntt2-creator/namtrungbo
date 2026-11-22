with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
for m in re.finditer(r'Trang', js):
    idx = m.start()
    print('--- Trang at', idx, '---')
    print(js[max(0, idx-40):min(len(js), idx+300)])

