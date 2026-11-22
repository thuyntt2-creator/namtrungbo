with open(r'C:\Users\lap4all\Desktop\New folder\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
matches = re.findall(r'@app\.route\([^\)]*\)[\s\S]*?def [^\(]+\([^\)]*\):[\s\S]*?return[^\n]+', code)
for m in matches:
    if 'hop' in m or 'index' in m:
        print(m[:300])
        print('-'*30)

