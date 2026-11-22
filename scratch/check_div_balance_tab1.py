with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

content_tab1 = "".join(lines[217:381]) # from tab-overview up to tab-volume
open_divs = content_tab1.count('<div')
close_divs = content_tab1.count('</div')
print(f"Tab 1 (lines 218-381): open={open_divs}, close={close_divs}, diff={open_divs - close_divs}")

content_tab2 = "".join(lines[381:481])
open_d2 = content_tab2.count('<div')
close_d2 = content_tab2.count('</div')
print(f"Tab 2 (lines 382-481): open={open_d2}, close={close_d2}, diff={open_d2 - close_d2}")

