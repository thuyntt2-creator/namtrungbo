with open(r'C:\Users\lap4all\Desktop\New folder\build_data_js.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '09_Rot LC' in l:
        print(f"09_Rot LC at line {i+1}")
        for j in range(i, min(len(lines), i+60)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break

