import json

data_path = r'C:\Users\lap4all\Desktop\New folder\data.json'
with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

cod = d.get('cod_report', {})
print('COD keys:', list(cod.keys()))
for k in ['title', 'summary_text', 'prev_period', 'curr_period', 'metrics']:
    print(k, ':', cod.get(k))

