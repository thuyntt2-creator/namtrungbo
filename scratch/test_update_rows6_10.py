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

cols = ['D', 'E', 'F', 'G', 'H', 'I', 'J']

# Prepare update for rows 6 to 10
updates = []
for r in range(6, 11):
    row_formulas = []
    # D to J
    for col in cols:
        f = f'=IFERROR((SUMIFS(raw!$J:$J,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$J:$J,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn"))/(SUMIFS(raw!$E:$E,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$E:$E,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn")),0)'
        row_formulas.append(f)
    # Col K
    f_k = f'=IFERROR(SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$J:$J, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$J:$J, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))) / SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$E:$E, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$E:$E, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))), 0)'
    row_formulas.append(f_k)
    updates.append(row_formulas)

ws_ntbo.update('D6:K10', updates, value_input_option='USER_ENTERED')
print("Updated D6:K10 successfully!")

time.sleep(3)

# Read back rows 6 to 10
res = ws_ntbo.get_values('A6:O10')
h = ws_ntbo.row_values(5)
for r in res:
    print(f"\nBC: {r[2]} ({r[0]})")
    for col_h, col_val in zip(h[3:15], r[3:15]):
        print(f"  {col_h}: {col_val}")

