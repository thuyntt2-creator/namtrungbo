with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'overview-insights-container' in line or 'banner-overview-bullets' in line:
        print(f'{i+1}: {line.strip()[:140]}')

