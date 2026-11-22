with open(r'C:\Users\lap4all\Desktop\New folder\data.json', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Lê Minh Lợi', text)]
print("Total occurrences of Lê Minh Lợi in data.json:", len(matches))
for m in matches[:5]:
    print(text[m-20:m+150])
    print('='*30)

