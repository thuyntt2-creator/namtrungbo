with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'#table-rot-tinh-detailed', text)]
print("Total matches:", len(matches))
for m in matches:
    print(text[m-20:m+500])
    print('='*50)

