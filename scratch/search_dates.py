import os, glob

root = r'C:\Users\lap4all\Desktop\New folder'
for dirpath, dirnames, filenames in os.walk(root):
    if '.git' in dirpath or 'node_modules' in dirpath:
        continue
    for fn in filenames:
        if fn.endswith(('.js', '.py', '.html', '.json')):
            p = os.path.join(dirpath, fn)
            try:
                txt = open(p, 'r', encoding='utf-8', errors='ignore').read()
                if '12/10' in txt or '16/09' in txt:
                    print(f'{p}: contains 12/10 or 16/09')
            except Exception:
                pass
