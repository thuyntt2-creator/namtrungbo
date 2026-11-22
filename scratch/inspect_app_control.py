with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== 9140-9220 ===')
for i in range(9140, min(9220, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== 9400-9520 ===')
for i in range(9400, min(9520, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

