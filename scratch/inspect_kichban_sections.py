with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-kichban"')
end_idx = text.find('</main>', idx)
tab_content = text[idx:end_idx]

import re
titles = re.findall(r'<div class="section-title">([^<]+)</div>', tab_content)
print(f"Total sections in tab-kichban: {len(titles)}")
for t in titles:
    print("-", t.strip())

