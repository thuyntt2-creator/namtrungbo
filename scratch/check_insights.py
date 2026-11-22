import json

with open(r'C:\Users\lap4all\Desktop\New folder\data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

ov = d.get('overview', {})
print('Insights in overview:')
for item in ov.get('insights', []):
    print('-', item)

