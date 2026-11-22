with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Sản lượng tăng mạnh' in line or 'banner-overview-bullets' in line or 'overview-insights-container' in line:
        print(f'{i+1}: {line.strip()[:140]}')

