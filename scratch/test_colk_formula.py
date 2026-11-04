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

# Test string comparison in SUMIFS on raw!$D:$D
# D5 is 2026-10-28, J5 is 2026-11-03
f_test1 = '=SUMIFS(raw!$E:$E, raw!$B:$B, $C6, raw!$D:$D, ">=" & TEXT($D$5, "yyyy-mm-dd"), raw!$D:$D, "<=" & TEXT($J$5, "yyyy-mm-dd") & "~")'
ws_ntbo.update_acell('Z6', f_test1)
time.sleep(2)
print("Result of test1 (raw!$D:$D >= text_d5 and <= text_j5):", ws_ntbo.acell('Z6').value)

# Also test sum over the 7 days directly:
# What if we sum the 7 days? Or does test1 return the exact sum?
# Let's clean Z6
ws_ntbo.update_acell('Z6', '')

