import json

with open(r'C:\Users\lap4all\Desktop\New folder\data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fd = d.get('fd', {})
print('FD keys:', list(fd.keys()))
print('FD summary:', fd.get('summary'))
print('Number of AMs:', len(fd.get('am', [])))
if fd.get('am'):
    print('Sample AM 0:', fd['am'][0])
    print('Sample AM 2 (Trang):', fd['am'][2] if len(fd['am']) > 2 else None)

