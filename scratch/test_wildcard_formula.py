import sys, gspread
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_ntbo = sh.worksheet('NTBo')

# Test placing formula in a temporary cell, e.g., Z6
test_formula = '=SUMIFS(raw!$E:$E, raw!$B:$B, $C6, raw!$D:$D, TEXT(J$5, "yyyy-mm-dd") & "*", raw!$C:$C, "Hàng Mới Ca 1")'
ws_ntbo.update_acell('Z6', test_formula)

import time
time.sleep(2)

val_z6 = ws_ntbo.acell('Z6').value
print("Formula test in Z6:", test_formula)
print("Result in Z6:", val_z6)

# Also test full GTC formula in Z7
full_formula = '=IFERROR((SUMIFS(raw!$J:$J,raw!$B:$B,$C6,raw!$D:$D,TEXT(J$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$J:$J,raw!$B:$B,$C6,raw!$D:$D,TEXT(J$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn"))/(SUMIFS(raw!$E:$E,raw!$B:$B,$C6,raw!$D:$D,TEXT(J$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$E:$E,raw!$B:$B,$C6,raw!$D:$D,TEXT(J$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn")),0)'
ws_ntbo.update_acell('Z7', full_formula)
time.sleep(2)
val_z7 = ws_ntbo.acell('Z7').value
print("Full formula test in Z7:", full_formula)
print("Result in Z7:", val_z7)

# Clean up Z6 and Z7
ws_ntbo.update_acell('Z6', '')
ws_ntbo.update_acell('Z7', '')
print("Cleaned up Z6 & Z7!")

