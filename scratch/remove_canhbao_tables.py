import os, re, time

root = r'C:\Users\lap4all\Desktop\New folder'
index_path = os.path.join(root, 'index.html')

with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove Tab 1 warning table
tab1_pat = r'<!-- CẢNH BÁO BẤT ỔN: BẢNG 13 BƯU CỤC TRONG NHÓM CẢNH BÁO -->\s*<div class="report-card"[\s\S]*?id="table-bc-canh-bao-overview"[\s\S]*?</div>\s*</div>\s*</div>'
if re.search(tab1_pat, html):
    html = re.sub(tab1_pat, '', html)
    print("Removed Tab 1 warning table.")
else:
    print("WARNING: tab1_pat not matched.")

# 2. Remove Tab 3 warning table
tab3_pat = r'<!-- ==================================================================== -->\s*<!-- BẢNG 3: BƯU CỤC TRONG NHÓM CẢNH BÁO BẤT ỔN \(GOOGLE SHEETS\) -->\s*<!-- ==================================================================== -->\s*<div class="report-card"[\s\S]*?id="table-bc-canh-bao"[\s\S]*?</div>\s*</div>\s*</div>'
if re.search(tab3_pat, html):
    html = re.sub(tab3_pat, '', html)
    print("Removed Tab 3 warning table.")
else:
    print("WARNING: tab3_pat not matched.")

# 3. Remove Tab 15 view if present
tab15_pat = r'<!-- ==================================================================== -->\s*<!-- TAB 15: BƯU CỤC TRONG NHÓM CẢNH BÁO BẤT ỔN \(GOOGLE SHEETS\) -->\s*<!-- ==================================================================== -->\s*<div class="tab-view" id="tab-bc-canhbao">[\s\S]*?</div>\s*</div>\s*</div>\s*</div>'
if re.search(tab15_pat, html):
    html = re.sub(tab15_pat, '', html)
    print("Removed Tab 15 warning view.")
else:
    print("WARNING: tab15_pat not matched.")

# Update cache bust timestamp
ts = int(time.time())
html = re.sub(r'data\.js\?v=\d+', f'data.js?v={ts}', html)
html = re.sub(r'app\.js\?v=\d+', f'app.js?v={ts}', html)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"index.html saved with cache bust v={ts}.")

