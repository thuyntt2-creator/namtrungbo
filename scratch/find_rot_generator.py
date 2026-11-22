import os

root = r'C:\Users\lap4all\Desktop\New folder'
for f in os.listdir(root):
    if f.endswith('.py'):
        path = os.path.join(root, f)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if '09_Rot LC' in c or ('rot_lc' in c and 'tinh' in c and 'am' in c):
                    print('Found:', f)
        except Exception:
            pass

