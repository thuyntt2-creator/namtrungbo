with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "tblBodyTinh && D.rot_lc.tinh" in l:
        print(f"Match at line {i+1}")
        for j in range(max(0, i-5), min(len(lines), i+45)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break

