with open(r'C:\Users\lap4all\Desktop\New folder\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '/kich-ban' in l:
        print(f"Line {i+1}: {l.strip()}")
        for j in range(i+1, min(len(lines), i+15)):
            print(f"  {lines[j].strip()}")
        print("="*40)

