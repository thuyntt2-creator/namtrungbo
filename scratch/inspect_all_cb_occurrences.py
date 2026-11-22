with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'BƯU CỤC TRONG NHÓM CẢNH BÁO' in line or 'table-bc-canh-bao' in line or 'table-bc-canh-bao-overview' in line:
        print(f'{i+1}: {line.strip()[:140]}')

