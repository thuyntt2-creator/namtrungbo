with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'id="tab-overview"' in l:
        print(f"tab-overview starts at line {i+1}")
    if 'id="tab-volume"' in l:
        print(f"tab-volume starts at line {i+1}")
    if 'id="tab-gtc-tong"' in l:
        print(f"tab-gtc-tong starts at line {i+1}")

