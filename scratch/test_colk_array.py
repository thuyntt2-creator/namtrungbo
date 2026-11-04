import sys, gspread
from google.oauth2.credentials import Credentials
import time

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_ntbo = sh.worksheet('NTBo')

# Test formulas for Col K
# Formula 1: Using SUM(SUMIFS(...))
f_k_test = '=IFERROR((SUM(INDEX(SUMIFS(raw!$J:$J,raw!$B:$B,$C6,raw!$C:$C,"Hàng Mới Ca 1",raw!$D:$D,TEXT($D$5:$J$5,"yyyy-mm-dd")&"*")))+SUM(INDEX(SUMIFS(raw!$J:$J,raw!$B:$B,$C6,raw!$C:$C,"Hàng Tồn",raw!$D:$D,TEXT($D$5:$J$5,"yyyy-mm-dd")&"*"))))/(SUM(INDEX(SUMIFS(raw!$E:$E,raw!$B:$B,$C6,raw!$C:$C,"Hàng Mới Ca 1",raw!$D:$D,TEXT($D$5:$J$5,"yyyy-mm-dd")&"*")))+SUM(INDEX(SUMIFS(raw!$E:$E,raw!$B:$B,$C6,raw!$C:$C,"Hàng Tồn",raw!$D:$D,TEXT($D$5:$J$5,"yyyy-mm-dd")&"*")))),0)'

ws_ntbo.update_acell('Z6', f_k_test)
time.sleep(2)
res_z6 = ws_ntbo.acell('Z6').value
print("Formula 1 result in Z6:", res_z6)

# Also test Formula 2: AVERAGE(D6:J6)
f_avg = '=AVERAGE(D6:J6)'
ws_ntbo.update_acell('Z7', f_avg)
time.sleep(1)
res_z7 = ws_ntbo.acell('Z7').value
print("Formula 2 (AVERAGE) in Z7:", res_z7)

ws_ntbo.update_acell('Z6', '')
ws_ntbo.update_acell('Z7', '')

