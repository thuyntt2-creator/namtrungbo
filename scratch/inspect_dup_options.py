with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(9430, 9490):
    if i < len(lines):
        print(f'{i+1}: {lines[i]}', end='')

