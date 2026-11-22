with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(5470, min(len(lines), 5580)):
    print(f'{i+1}: {lines[i]}', end='')

