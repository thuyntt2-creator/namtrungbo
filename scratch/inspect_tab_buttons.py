with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = re.findall(r'<button[^>]*data-tab="[^"]*"[^>]*>[\s\S]*?</button>', html[:20000])
for m in matches:
    print(m.strip().replace('\n', ' '))

