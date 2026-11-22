with open(r'C:\Users\lap4all\Desktop\New folder\KICH_BAN_THUYET_TRINH_W45_NAM_TRUNG_BO.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Length of HTML:", len(text))
# Check some key data points
checks = [
    '370.221', '97.861', '64,1%', '64,5%', '95,2%', '96,2%',
    '91,9%', '95,7%', '1,2%', '86,3%', '6,2%', '4,1%', '87,7 Tr'
]
for c in checks:
    print(f"'{c}' in text:", c in text)

