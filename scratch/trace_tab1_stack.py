with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
for i in range(217, 381):
    line = lines[i]
    # find open divs and close divs in order
    import re
    tokens = re.findall(r'(<div[^>]*>|</div)', line)
    for t in tokens:
        if t == '</div':
            if stack:
                popped = stack.pop()
            else:
                print(f"Underflow at line {i+1}")
        else:
            # extract id or class
            id_m = re.search(r'id="([^"]+)"', t)
            cls_m = re.search(r'class="([^"]+)"', t)
            desc = (id_m.group(1) if id_m else '') or (cls_m.group(1) if cls_m else t)
            stack.append((i+1, desc))

print("Unclosed divs at end of Tab 1:")
for line_no, desc in stack:
    print(f"Line {line_no}: {desc}")

