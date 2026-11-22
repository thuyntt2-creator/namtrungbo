with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== LINES 370 - 435 ===')
for i in range(370, min(len(lines), 435)):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== LINES 780 - 845 ===')
for i in range(780, min(len(lines), 845)):
    print(f'{i+1}: {lines[i]}', end='')

