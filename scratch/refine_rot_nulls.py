import json, time, re

data_json_path = r'C:\Users\lap4all\Desktop\New folder\data.json'
with open(data_json_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

for a in d['rot_lc']['am']:
    if a['am'] == 'Lê Minh Lợi':
        a['diff'] = None
        a['w44'] = None
        a['w_prev'] = None
        a['w37'] = None
    elif a['am'] == 'Huỳnh Trúc Duyên':
        a['diff'] = None
        a['w44'] = None
        a['w45'] = None
        a['w_prev'] = None
        a['w_curr'] = None
        a['w37'] = None
        a['w38'] = None

with open(data_json_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

data_js_path = r'C:\Users\lap4all\Desktop\New folder\data.js'
with open(data_js_path, 'w', encoding='utf-8') as f:
    f.write("window.DASHBOARD_DATA = " + json.dumps(d, ensure_ascii=False) + ";\n")
    f.write("window.DATA = window.DASHBOARD_DATA;\n")
    f.write("const REPORT_DATA = window.DASHBOARD_DATA;\n")
    f.write("const D = window.DASHBOARD_DATA;\n")

# Update cache bust in index.html
index_path = r'C:\Users\lap4all\Desktop\New folder\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

ts = int(time.time())
html = re.sub(r'data\.js\?v=\d+', f'data.js?v={ts}', html)
html = re.sub(r'app\.js\?v=\d+', f'app.js?v={ts}', html)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated data.json, data.js and cache bust successfully!")

