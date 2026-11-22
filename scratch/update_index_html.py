import re, os, time

root = r'C:\Users\lap4all\Desktop\New folder'
index_path = os.path.join(root, 'index.html')

with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove #banner-overview-bullets
banner_bullets_pat = r'\s*<!-- 5 Key Analysis Bullets \(KHỐI ĐIỂM NỔI BẬT & ĐÁNH GIÁ W45\) -->\s*<div id="banner-overview-bullets"[\s\S]*?</div>\s*</div>\s*(?=<!-- 10 Key Metric Tiles)'
if re.search(banner_bullets_pat, html):
    html = re.sub(banner_bullets_pat, '\n      </div>\n    </div>\n', html)
    print("Removed #banner-overview-bullets.")
else:
    # Try more generic pattern
    gen_pat = r'\s*<div id="banner-overview-bullets"[\s\S]*?</div>\s*</div>\s*(?=<!-- 10 Key Metric Tiles)'
    if re.search(gen_pat, html):
        html = re.sub(gen_pat, '\n      </div>\n    </div>\n', html)
        print("Removed #banner-overview-bullets (generic).")
    else:
        print("WARNING: banner_bullets_pat not matched.")

# 2. Replace static dots with commas in numbers
replacements = [
    ('64.1%', '64,1%'),
    ('87.7 Tr', '87,7 Tr'),
    ('+34.5%', '+34,5%'),
    ('34.5%', '34,5%'),
    ('64.5%', '64,5%'),
    ('95.2%', '95,2%'),
    ('91.9%', '91,9%'),
    ('1.2%', '1,2%'),
    ('87.0%', '87,0%'),
    ('63.5%', '63,5%'),
    ('8.5 Tr', '8,5 Tr'),
    ('62.0%', '62,0%'),
    ('76.0%', '76,0%'),
    ('90.0%', '90,0%'),
    ('92.0%', '92,0%'),
    ('6.5%', '6,5%'),
    ('0.3%p', '0,3%p'),
    ('-0.3%p', '-0,3%p'),
    ('4.1%', '4,1%'),
    ('4.8%', '4,8%'),
    ('0.7%p', '0,7%p'),
    ('-0.7%p', '-0,7%p'),
    ('86.3%', '86,3%'),
    ('82.3%', '82,3%'),
    ('4.0%p', '4,0%p'),
    ('+4.0%p', '+4,0%p'),
    ('95.1%', '95,1%'),
    ('72.5%', '72,5%'),
    ('65.2 Tr', '65,2 Tr'),
    ('22.5 Tr', '22,5 Tr'),
    ('40.0%', '40,0%'),
    ('41.3%', '41,3%'),
    ('1.3%p', '1,3%p'),
    ('+1.3%p', '+1,3%p'),
    ('1.3%', '1,3%'),
    ('0.0%p', '0,0%p'),
    ('86,99%', '87,0%'),
    ('95,23%', '95,2%'),
    ('64,86%', '64,1%'),
    ('91,89%', '91,9%'),
    ('1,18%', '1,2%'),
    ('+0.49%p', '+0,5%p'),
    ('-0.79%p', '-0,8%p'),
    ('-0,79%p', '-0,8%p'),
    ('+0,49%p', '+0,5%p'),
    ('64.86%', '64,1%'),
]

for old, new in replacements:
    html = html.replace(old, new)

# 3. Update cache buster
ts = int(time.time())
html = re.sub(r'data\.js\?v=\d+', f'data.js?v={ts}', html)
html = re.sub(r'app\.js\?v=\d+', f'app.js?v={ts}', html)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"index.html updated successfully with cache bust v={ts}.")

