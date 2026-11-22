with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'chart-rot-lc-bar' in l:
        print(f"Chart at line {i+1}")
        for j in range(i, min(len(lines), i+60)):
            print(f"  {lines[j].rstrip()}")
        break

