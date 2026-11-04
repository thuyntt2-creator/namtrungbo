import sys, gspread
from google.oauth2.credentials import Credentials
import datetime

sys.stdout.reconfigure(encoding='utf-8')
creds = Credentials.from_authorized_user_file('authorized_user.json', [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
ws_raw = sh.worksheet('raw')

raw_data = ws_raw.get_all_values()
# Row 0 is header: ['Cấp Quản Lý', 'Chi tiết', 'Loại Hàng', 'Time', 'Volume', ...]
# Col 1: Chi tiet (BC name)
# Col 2: Loai Hang ("Hàng Mới Ca 1", "Hàng Tồn")
# Col 3: Time
# Col 4: Volume (E)
# Col 9: GTC (J)

# Let's calculate for Đức Trọng 1 on 2026-11-03
gtc_sum = 0
vol_sum = 0
for r in raw_data[1:]:
    bc = r[1]
    lh = r[2]
    time_str = r[3].split(' - ')[0].strip() # strip the ' - Thứ ...'
    if '(LDO) Đức Trọng 1' in bc and time_str == '2026-11-03' and lh in ['Hàng Mới Ca 1', 'Hàng Tồn']:
        try:
            vol = float(r[4].replace(',', ''))
            gtc = float(r[9].replace(',', ''))
            gtc_sum += gtc
            vol_sum += vol
            print(f"Row: {lh} | Vol: {vol} | GTC: {gtc}")
        except Exception as e:
            print("Error parsing row:", r, e)

print(f"\nĐức Trọng 1 on 2026-11-03:")
print(f"Total GTC: {gtc_sum}, Total Vol: {vol_sum}")
if vol_sum > 0:
    print(f"%GTC = {gtc_sum / vol_sum * 100:.2f}%")
