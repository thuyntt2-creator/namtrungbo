with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if any(k in line for k in ['kpi-cod-total', 'cod-banner-title', 'BÁO CÁO COD', 'th-cod-prev', 'th-cod-curr', 'Tuần W42', 'Tuần N']):
        print(f'{i+1}: {line.strip()[:140]}')

