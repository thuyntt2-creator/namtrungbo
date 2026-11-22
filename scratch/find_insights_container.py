with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'overview-insights-container' in line:
        print(f'{i+1}: {line.strip()[:140]}')
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f'  {j+1}: {lines[j]}', end='')

