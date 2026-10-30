import openpyxl

wb = openpyxl.load_workbook(r'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx')
ws = wb['chat_luong_lay']
ws['J6'] = '=_xlfn.MAXIFS(canh_bao!$I$10:$I$178, canh_bao!$B$10:$B$178, A6)'
wb.save(r'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx')
print('Saved test _xlfn.MAXIFS')

