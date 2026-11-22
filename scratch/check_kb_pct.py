with open(r'C:\Users\lap4all\Desktop\New folder\KICH_BAN_THUYET_TRINH_W45_NAM_TRUNG_BO.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'(\d+[.,]\d+%)', text)
print("Sample percentages:", set(matches[:25]))

checks_dot = [
    '64.1%', '64.86%', '95.23%', '91.89%', '87.7 Tr', '241.6 Tr', '1.18%', '1.2%'
]
for c in checks_dot:
    print(f"'{c}' in text:", c in text)

