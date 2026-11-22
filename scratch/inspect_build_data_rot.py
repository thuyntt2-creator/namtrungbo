with open(r'C:\Users\lap4all\Desktop\New folder\build_data_js.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'rot_lc', text)]
for m in matches:
    print(text[m-50:m+400])
    print('='*50)

