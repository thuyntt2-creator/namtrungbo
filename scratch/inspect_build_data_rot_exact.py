with open(r'C:\Users\lap4all\Desktop\New folder\build_data_js.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "'rot_lc'" in l or 'ws_rot' in l or '09_Rot LC' in l:
        for j in range(max(0, i-50), min(len(lines), i+60)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break

