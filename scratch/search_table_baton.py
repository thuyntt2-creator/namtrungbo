import os, re

root = r'C:\Users\lap4all\Desktop\New folder'

for fn in ['index.html', 'app.js']:
    p = os.path.join(root, fn)
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = [m.start() for m in re.finditer(r'CẢNH BÁO BẤT ỔN|canh_bao|bc_canh_bao|table-bc-canh-bao', content, re.IGNORECASE)]
    print(f'{fn}: found {len(matches)} matches')
    for idx in matches[:5]:
        print(f'  Match at {idx}:')
        print(content[max(0, idx-50):min(len(content), idx+200)])
        print('-'*40)

