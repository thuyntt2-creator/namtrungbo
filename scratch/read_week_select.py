with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(160, 220):
    if i < len(lines):
        print(f'{i+1}: {lines[i]}', end='')

