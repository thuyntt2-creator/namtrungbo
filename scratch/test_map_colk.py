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

f_map = '=IFERROR(SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$J:$J, raw!$B:$B, $C6, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$J:$J, raw!$B:$B, $C6, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))) / SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$E:$E, raw!$B:$B, $C6, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$E:$E, raw!$B:$B, $C6, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))), 0)'

ws_ntbo.update_acell('Z6', f_map)
time.sleep(2)
res_z6 = ws_ntbo.acell('Z6').value
print("MAP formula result in Z6:", res_z6)

ws_ntbo.update_acell('Z6', '')

