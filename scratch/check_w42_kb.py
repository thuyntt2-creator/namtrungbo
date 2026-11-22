for fname in ['tab_kichban_w45.html', 'KICH_BAN_THUYET_TRINH_W45_NAM_TRUNG_BO.html']:
    with open(r'C:\Users\lap4all\Desktop\New folder\\' + fname, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"{fname}: W42 count = {text.count('W42')}")

