import json

with open('scratch/fd_calculated_results.json', encoding='utf-8') as f:
    res = json.load(f)

for am in res['am']:
    if 'Trang' in am['am_name']:
        print("AM Trang:", json.dumps(am, ensure_ascii=False, indent=2))

for bc in res['top_bc']:
    if 'Lâm Viên - Đà Lạt 2' in bc['bc']:
        print("Lâm Viên - Đà Lạt 2:", json.dumps(bc, ensure_ascii=False, indent=2))
