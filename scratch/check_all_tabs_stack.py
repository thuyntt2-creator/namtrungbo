with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import re

# Find all tab-view definitions
tabs = []
for i, l in enumerate(lines):
    m = re.search(r'<div class="tab-view[^"]*" id="([^"]+)"', l)
    if m:
        tabs.append((i, m.group(1)))

print("Found tabs:", [t[1] for t in tabs])

for idx in range(len(tabs)):
    start_line, tab_id = tabs[idx]
    end_line = tabs[idx+1][0] if idx+1 < len(tabs) else len(lines)
    
    stack = []
    for line_idx in range(start_line, end_line):
        tokens = re.findall(r'(<div[^>]*>|</div)', lines[line_idx])
        for t in tokens:
            if t == '</div':
                if stack:
                    stack.pop()
                else:
                    print(f"[{tab_id}] Extra closing div at line {line_idx+1}")
            else:
                id_m = re.search(r'id="([^"]+)"', t)
                cls_m = re.search(r'class="([^"]+)"', t)
                desc = (id_m.group(1) if id_m else '') or (cls_m.group(1) if cls_m else t)
                stack.append((line_idx+1, desc))
    
    if stack:
        print(f"[{tab_id}] UNCLOSED DIVS ({len(stack)}):", stack[:3])
    else:
        print(f"[{tab_id}] PERFECTLY BALANCED!")

