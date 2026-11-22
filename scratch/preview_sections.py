with open(r'C:\Users\lap4all\Desktop\New folder\KICH_BAN_THUYET_TRINH_W45_NAM_TRUNG_BO.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
sections = re.findall(r'<div class="section-title">([^<]+)</div>\s*<div class="callout-box">([\s\S]*?)</div>', text)
print(f"Extracted {len(sections)} sections")
for i, (title, content) in enumerate(sections):
    # clean tags
    clean_txt = re.sub(r'<[^>]+>', '', content).strip()
    print(f"=== Section {i+1}: {title.strip()} ===")
    print(clean_txt[:250] + "...\n")

