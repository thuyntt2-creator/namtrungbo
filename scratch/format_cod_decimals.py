import json, os

root = r'C:\Users\lap4all\Desktop\New folder'
json_path = os.path.join(root, 'data.json')
js_path = os.path.join(root, 'data.js')

with open(json_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

cod = d.get('cod_report', {})
if 'metrics' in cod:
    for m in cod['metrics']:
        for k in ['prev', 'curr', 'diff_val', 'diff_pct']:
            if k in m and isinstance(m[k], str):
                val = m[k]
                # convert e.g. 576,404.7 to 576.404,7
                if ',' in val and '.' in val:
                    val = val.replace(',', '_temp_').replace('.', ',').replace('_temp_', '.')
                elif '.' in val:
                    val = val.replace('.', ',')
                m[k] = val

if 'am_comparison' in cod:
    for item in cod['am_comparison']:
        for k in ['prev_tm', 'curr_tm', 'diff', 'trend']:
            if k in item and isinstance(item[k], str):
                item[k] = item[k].replace('.', ',')

if 'bc_details' in cod:
    for item in cod['bc_details']:
        for k in ['prev_tm', 'curr_tm', 'diff', 'cash_m']:
            if k in item and isinstance(item[k], str):
                item[k] = item[k].replace('.', ',')

if 'actions' in cod:
    for item in cod['actions']:
        for k in ['prev_tm', 'curr_tm', 'diff']:
            if k in item and isinstance(item[k], str):
                item[k] = item[k].replace('.', ',')

cod['prev_period'] = 'Tuần W44 (26/10 – 01/11)'
cod['curr_period'] = 'Tuần W45 (02/11 – 08/11)'
cod['summary_text'] = 'Tuần W44 (26/10 – 01/11): 40,0% TM   ➔   Tuần W45 (02/11 – 08/11): 41,3% TM   |   Biến động: +1,3%p (Xấu đi ⚠️)'

d['cod_report'] = cod

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write('const D = ' + json.dumps(d, ensure_ascii=False, indent=2) + ';\n')

print("data.json and data.js cod_report numbers formatted with VN decimal comma.")

