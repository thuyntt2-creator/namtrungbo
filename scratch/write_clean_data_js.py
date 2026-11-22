import json, os

root = r'C:\Users\lap4all\Desktop\New folder'
json_path = os.path.join(root, 'data.json')
js_path = os.path.join(root, 'data.js')

with open(json_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

am_name_map = {
    'AM Lợi': 'Lê Minh Lợi',
    'AM Linh': 'Trương Quang Linh',
    'AM Trang': 'Trần Nguyễn Huyền Trang',
    'AM Nhung': 'Trần Thị Nhung',
    'AM Phong': 'Lê Hồng Phong',
    'AM Long': 'Nguyễn Thanh Long',
    'AM Vũ': 'Nguyễn Lê Nguyên Vũ',
    'AM Duy': 'Phan Đình Duy',
    'AM Nhi': 'Phan Nguyễn Yến Nhi',
    'AM Chi': 'Huỳnh Thị Kim Chi',
    'AM Thư': 'Thái Thị Thanh Thư',
    'AM Trường': 'Lê Văn Trường',
    'AM Phi': 'Nguyễn Hoàng Phi',
    'AM D.Long': 'Nguyễn Duy Long',
    'AM Thơ': 'Nguyễn Thị Tuyết Thơ',
    'AM Nghĩa': 'Nguyễn Đỗ Minh Nghĩa',
    'AM Nhựt': 'Lê Thanh Nhựt',
    'AM Nga': 'Hồng Bích Nga',
    'AM Thủy': 'Cao Thị Thanh Thủy',
    'AM Khánh': 'Nguyễn Ngọc Khánh',
    'Lê Thị Kim Chi': 'Huỳnh Thị Kim Chi'
}

w44_rates = {
    'Lê Minh Lợi': 0.1466,
    'Trương Quang Linh': 0.0866,
    'Trần Nguyễn Huyền Trang': None,
    'Trần Thị Nhung': 0.0770,
    'Lê Hồng Phong': 0.0808,
    'Nguyễn Thanh Long': 0.0751,
    'Nguyễn Lê Nguyên Vũ': 0.0757,
    'Phan Đình Duy': 0.0853,
    'Phan Nguyễn Yến Nhi': 0.0947,
    'Huỳnh Thị Kim Chi': 0.0575,
    'Thái Thị Thanh Thư': 0.0596,
    'Lê Văn Trường': 0.0627,
    'Nguyễn Hoàng Phi': 0.0708,
    'Nguyễn Duy Long': 0.0622,
    'Nguyễn Thị Tuyết Thơ': 0.0512,
    'Nguyễn Đỗ Minh Nghĩa': 0.0586,
    'Lê Thanh Nhựt': 0.0587,
    'Hồng Bích Nga': 0.0569,
    'Cao Thị Thanh Thủy': 0.0577,
    'Nguyễn Ngọc Khánh': 0.0452,
}

if 'fd' in d and 'am' in d['fd']:
    updated_am = []
    for item in d['fd']['am']:
        old_name = item.get('am', '')
        full_name = am_name_map.get(old_name, old_name)
        item['am'] = full_name
        
        if full_name in w44_rates:
            item['rate_full_prev'] = w44_rates[full_name]
            if w44_rates[full_name] is not None and item.get('rate_full') is not None:
                item['diff_full'] = round(item['rate_full'] - w44_rates[full_name], 4)
            else:
                item['diff_full'] = None
        
        if full_name == 'Trần Nguyễn Huyền Trang':
            item['rate_full_prev'] = None
            item['diff_full'] = None
            item['rate_tts_prev'] = None
            item['diff_tts'] = None

        updated_am.append(item)

    # Sort descending by rate_full (W45)
    updated_am.sort(key=lambda x: x.get('rate_full', 0) if x.get('rate_full') is not None else 0, reverse=True)
    for idx, item in enumerate(updated_am):
        item['stt'] = idx + 1
    d['fd']['am'] = updated_am

# Ensure meta has latest_week: W45, prev_week: W44
if 'meta' not in d:
    d['meta'] = {}
d['meta']['latest_week'] = 'W45'
d['meta']['prev_week'] = 'W44'

# Save to data.json
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("Saved data.json successfully.")

# Save to data.js with window.DASHBOARD_DATA =
with open(js_path, 'w', encoding='utf-8') as f:
    f.write('window.DASHBOARD_DATA = ' + json.dumps(d, ensure_ascii=False) + ';\nwindow.DATA = window.DASHBOARD_DATA;\nconst REPORT_DATA = window.DASHBOARD_DATA;\nconst D = window.DASHBOARD_DATA;\n')
print("Saved data.js successfully.")

