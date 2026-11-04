# -*- coding: utf-8 -*-
with open('AGENTS.md', 'r', encoding='utf-8') as f:
    text = f.read()

target = '## 7. CÁC NGUYÊN TẮC HỌC TẬP TỰ ĐỘNG TỪ CHỊ THỦY'
new_item = """13. **Cảnh Báo Quá Hạn Mốc 11h Trưa (Đôn Đốc Xử Lý Ca Sáng NTB):**
    * URL: https://docs.google.com/spreadsheets/d/1MeNHjrz8R59E03vx6oRWuWBpsbBVQFEsEdxMyv242nY/edit?gid=963649240#gid=963649240
    * Sheet ID: 1MeNHjrz8R59E03vx6oRWuWBpsbBVQFEsEdxMyv242nY | GID: 963649240
    * Tab: quá hạn_NTB
    * Cấu trúc cột chuẩn: **Cột B = Mã Vận Đơn (MVĐ / order_code)**, **Cột M = Tên AM chuẩn (AM)**, Cột J = Bưu cục (buu_cuc), Cột E = Trạng thái (status_d0), Cột C = Loại đơn/Sàn (client_group), Cột D = aging.
    * Script xử lý & push GTalk kèm rung chuông: `python push_don_tts_am.py` (hoặc chạy 1-click `CHAY_CANH_BAO_QUA_HAN_11H.bat`). Thêm `--send` để gửi thật, `--am "Tên AM"` để lọc riêng.

---

"""

for line in text.splitlines():
    if target in line:
        text = text.replace(line, new_item + line)
        break

with open('AGENTS.md', 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated AGENTS.md successfully')

