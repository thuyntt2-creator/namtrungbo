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

# Total rows with BC
col_c = ws_ntbo.col_values(3)
last_row = len(col_c)
print(f"Total rows to update: 6 to {last_row} (total {last_row - 5} bưu cục)")

cols = ['D', 'E', 'F', 'G', 'H', 'I', 'J']

all_updates = []
for r in range(6, last_row + 1):
    row_formulas = []
    # D to J (7 days)
    for col in cols:
        f = f'=IFERROR((SUMIFS(raw!$J:$J,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$J:$J,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn"))/(SUMIFS(raw!$E:$E,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Mới Ca 1")+SUMIFS(raw!$E:$E,raw!$B:$B,$C{r},raw!$D:$D,TEXT({col}$5,"yyyy-mm-dd")&"*",raw!$C:$C,"Hàng Tồn")),0)'
        row_formulas.append(f)
    # Col K (%GTC 7 ngày)
    f_k = f'=IFERROR(SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$J:$J, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$J:$J, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))) / SUM(MAP($D$5:$J$5, LAMBDA(d, SUMIFS(raw!$E:$E, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Mới Ca 1", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*") + SUMIFS(raw!$E:$E, raw!$B:$B, $C{r}, raw!$C:$C, "Hàng Tồn", raw!$D:$D, TEXT(d, "yyyy-mm-dd") & "*")))), 0)'
    row_formulas.append(f_k)
    all_updates.append(row_formulas)

target_range = f'D6:K{last_row}'
print(f"Updating range {target_range} with {len(all_updates)} rows...")
ws_ntbo.update(values=all_updates, range_name=target_range, value_input_option='USER_ENTERED')
print("Successfully updated all rows in NTBo!")

# Wait for Google Sheets calculation
time.sleep(4)

# Check cell J2 (Tổng số lượng bưu cục cảnh báo)
total_alert = ws_ntbo.acell('J2').value
print(f"\nTổng số lượng bưu cục cảnh báo (Cell J2): {total_alert}")

# Print list of alert BCs
rows_data = ws_ntbo.get_values(f'A6:O{last_row}')
alerts = []
for r in rows_data:
    status = r[13] if len(r) > 13 else ""
    if status == 'Nằm TOP Bất ổn':
        alerts.append((r[0], r[1], r[2], r[9], r[10], r[11], r[12], r[14]))

print(f"\nDanh sách bưu cục 'Nằm TOP Bất ổn' ({len(alerts)} bưu cục):")
for am, bc_id, bc_name, gtc_n1, gtc_7d, gtc_best, so_sanh, ly_do in alerts:
    print(f"  - {bc_name:<30} | AM: {am:<22} | 03/11: {gtc_n1:<7} | 7D: {gtc_7d:<7} | Best: {gtc_best:<7} | SS: {so_sanh:<7} | Lý do: {ly_do}")

