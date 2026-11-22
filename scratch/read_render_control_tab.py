with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
idx = js.find('function renderControlTab()')
print(js[idx:idx+3500])

