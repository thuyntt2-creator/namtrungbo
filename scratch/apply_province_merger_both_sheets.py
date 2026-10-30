import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from copy import copy

paths = [
    r'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx',
    r'c:\Users\lap4all\Desktop\New folder\Capacity_Planning_Test\[GHN]_Capacity Planning_Test_T10.2026\BAO_CAO_CAPACITY_11.11_FINAL.xlsx'
]

# Styling definitions
navy_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
slate_fill = PatternFill(start_color="204A6E", end_color="204A6E", fill_type="solid")
white_bold_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
regular_font = Font(name="Segoe UI", size=10)
bold_font = Font(name="Segoe UI", size=10, bold=True)

# Data for cap_hieu_chinh
tay_lam_cap = [
    ('Bến Sỏi', 'Tây Lâm', 1542, 'don', 22, 11.9, '=ROUND(C{r}/(E{r}*1.1), 1)', '=ROUND(F{r}*G{r}*1.1, 0)', '❌ KHÔNG DÙNG ĐƯỢC', 'BẪY NGHỈ VIỆC: Đo lúc 22 NV. Thực tế 7 ngày qua chỉ còn 11.9 NV đi làm (hụt 10 người). Cap thực tế sụt còn 822 - 834 đơn. Tin cap cũ là vỡ trận!'),
    ('Cầu Mây', 'Tây Lâm', 910, 'don', 14, 15.6, 65.5, '=ROUND(F{r}*G{r}*1.1, 0)', '⚠️ CẦN CẬP NHẬT', 'Cap 910 đo lúc 14 NV. Bưu cục đã có 15.6 NV và NS tăng lên 65.5 -> Năng lực thực tế là 1.124 đơn (trưởng bưu cục kêu vượt cap vì so với số cũ).'),
    ('Gò Đào', 'Tây Lâm', 1996, 'don', 27, 24.9, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC', 'Năng lực dồi dào, đóng vai trò bưu cục đệm nhận tải hỗ trợ cho Bến Sỏi.'),
    ('Lâm Viên 1', 'Tây Lâm', 1745, 'don', 24, 14.9, 56.5, '=ROUND(F{r}*G{r}*1.1, 0)', '❌ KHÔNG DÙNG ĐƯỢC', 'BẪY TÁCH BƯU CỤC: Đo từ tháng 9 lúc 24 NV. Từ 25/10 đã tách 6 NV sang Lâm Viên 2, hiện còn 15 NV -> Cap thật sụt còn 926 - 932 đơn.'),
    ('Lâm Viên 2', 'Tây Lâm', 417, 'don', 8, 7.3, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '⚠️ LOW DATA', 'Bản đo mới 9 ngày, nhân sự mới lạ đường (NS 47.4 đơn/người). Đang tăng dần khi quen đường.'),
    ('Rạch Sen', 'Tây Lâm', 1232, 'don', 18, 16.7, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC', 'Nhân sự và năng suất ổn định, sai số dưới 5% so với bản đo.')
]

bac_hoa_cap = [
    ('CK Bắc Hòa', 'Bắc Hòa', 2600, 'energy', 20, 18.4, 8, '=ROUND(C{r}/G{r}, 0)', '❌ KHÔNG DÙNG ĐƯỢC', 'BẪY ĐƠN VỊ: 2.600 là energy, không phải đơn. Định mức 8 energy/đơn -> Cap thật chỉ 325 đơn/ngày. Đơn về 405 đơn là VƯỢT CAP 24.6%.'),
    ('Đồng Tre', 'Bắc Hòa', 1333, 'don', 19, 17.3, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC', 'Số đo chuẩn, năng lực đáp ứng tốt, chỉ chạm nhẹ cap ngày 12/11.'),
    ('Hòa Lộc', 'Bắc Hòa', 1184, 'don', 17, 16.0, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC (GIAO)', 'Chiều giao ổn định (cap 1.184), nhưng bị khủng hoảng chiều lấy (OPR rớt 65.5%).'),
    ('Kênh Đào', 'Bắc Hòa', 1608, 'don', 24, 22.6, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC', 'Năng lực dư thừa, có thể hỗ trợ lấy hàng và giao hàng cho bưu cục lân cận.'),
    ('Phú Điền', 'Bắc Hòa', 1409, 'don', 19, 17.9, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '⚠️ NGHẼN HẠ TẦNG', 'BẪY MẶT BẰNG & LỊCH XE: Cap lý thuyết đủ, nhưng nghẽn sàn chia hàng 90m2 và xe KTC đến trễ 10h. Thêm người không giải quyết được.'),
    ('Suối Ngọc', 'Bắc Hòa', 1594, 'don', 23, 21.7, '=ROUND(C{r}/(E{r}*1.1), 1)', '=C{r}', '✅ DÙNG ĐƯỢC', 'Vận hành ổn định, phối hợp tuyến giáp ranh với Kênh Đào hiệu quả.')
]

# Data for chat_luong_lay
tay_lam_lay = [
    ('Bến Sỏi', 'Tây Lâm', 1081, 780, 0.932, 0.786, 779, '🟢 CHẤT LƯỢNG GIỮ, NGUY CƠ THIẾU NGƯỜI', 'Vượt trần 3 ngày (Peak 1.294 đơn, vượt 19.7%). Rủi ro lớn do thiếu shipper.'),
    ('Cầu Mây', 'Tây Lâm', 989, 691, 0.936, 0.784, 685, '🟢 GIỮ ỔN ĐỊNH (OPR 78.4%, LTC 93.6%)', 'Vượt trần 3 ngày Thứ Hai và D-Day (Peak 1.145 đơn, vượt 15.8%).'),
    ('Gò Đào', 'Tây Lâm', 1207, 855, 0.933, 0.779, 854, '🟢 GIỮ ỔN ĐỊNH (OPR 77.9%, LTC 93.3%)', 'Vượt trần 3 ngày (Peak 1.437 đơn, vượt 19.1%).'),
    ('Lâm Viên 1', 'Tây Lâm', 1300, 922, 0.933, 0.780, 908, '🟢 GIỮ ỔN ĐỊNH (OPR 78.0%, LTC 93.3%)', 'Vượt trần 3 ngày (Peak 1.571 đơn, vượt 20.8%). Cần đo lại trần sau tách LV2.'),
    ('Lâm Viên 2', 'Tây Lâm', 'Chưa đo', 0, 'Chưa đo', 'Chưa đo', 0, '⚪ CHƯA THIẾT LẬP TRẦN LẤY', 'Mới tách bưu cục từ 25/10, chưa có dữ liệu đo trần lấy.'),
    ('Rạch Sen', 'Tây Lâm', 1005, 777, 0.935, 0.781, 779, '🟢 GIỮ ỔN ĐỊNH (OPR 78.1%, LTC 93.5%)', 'Vượt trần 4 ngày Thứ Hai và D-Day (Peak 1.298 đơn, vượt 29.2%).')
]

bac_hoa_lay = [
    ('CK Bắc Hòa', 'Bắc Hòa', 200, 120, 0.933, 0.783, 119, '🟢 AN TOÀN (OPR 78.3%, LTC 93.3%)', 'An toàn tuyệt đối, không vượt trần lấy (Peak 185/200).'),
    ('Đồng Tre', 'Bắc Hòa', 1196, 1003, 0.935, 0.783, 997, '🟢 GIỮ ỔN ĐỊNH (OPR 78.3%, LTC 93.5%)', 'Vượt trần các ngày Thứ Hai và D-Day (Peak 1.719 đơn, vượt 43.7%).'),
    ('Hòa Lộc', 'Bắc Hòa', 847, 814, 0.875, 0.656, 811, '🔴 TỤT DỐC NGHIÊM TRỌNG (OPR sụt từ 78% còn 65.5%, %LTC còn 87.5%)', 'VƯỢT TRẦN 10/14 NGÀY (Peak 1.533 đơn, vượt 81%). Trưởng BC báo cáo sai lệch!'),
    ('Kênh Đào', 'Bắc Hòa', 935, 657, 0.934, 0.785, 630, '🟢 GIỮ ỔN ĐỊNH (OPR 78.5%, LTC 93.4%)', 'Vượt trần nhẹ các ngày cao điểm (Peak 1.114 đơn, vượt 19.1%).'),
    ('Phú Điền', 'Bắc Hòa', 1034, 792, 0.934, 0.790, 780, '🟢 GIỮ ỔN ĐỊNH (OPR 79.0%, LTC 93.4%)', 'Vượt trần 4 ngày (Peak 1.334 đơn, vượt 29.0%).'),
    ('Suối Ngọc', 'Bắc Hòa', 1055, 757, 0.931, 0.781, 729, '🟢 GIỮ ỔN ĐỊNH (OPR 78.1%, LTC 93.1%)', 'Vượt trần nhẹ các ngày cao điểm (Peak 1.246 đơn, vượt 18.1%).')
]

for p in paths:
    wb = openpyxl.load_workbook(p)
    
    # ----------------------------------------------------
    # 1. UPGRADE SHEET cap_hieu_chinh
    # ----------------------------------------------------
    ws_cap = wb['cap_hieu_chinh']
    # Clear existing rows 4 to 25
    for r in range(4, 26):
        for c in range(1, 12):
            ws_cap.cell(r, c).value = None
            ws_cap.cell(r, c).fill = PatternFill(fill_type=None)
            ws_cap.cell(r, c).border = Border()
    # Unmerge any old merges in rows 4-25
    for m in list(ws_cap.merged_cells.ranges):
        if m.min_row >= 4:
            ws_cap.unmerge_cells(str(m))
            
    # Row 4: Headers
    headers_cap = ['Bưu Cục', 'Tỉnh', 'Cap Trong File', 'Đơn Vị', 'NV Lúc Đo', 'NV Thực Tế', 'Năng Suất Chuẩn (đơn/người)', 'Cap Thực Tế Hiệu Chỉnh', 'Trạng Thái Dùng Được?', 'Bằng Chứng Dữ Liệu & Giải Thích Chuyên Môn']
    for c, h in enumerate(headers_cap, 1):
        cell = ws_cap.cell(4, c, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws_cap.row_dimensions[4].height = 28
    
    # Row 5: Section Header TÂY LÂM
    ws_cap.merge_cells('A5:J5')
    cell_tl = ws_cap.cell(5, 1, 'TỈNH TÂY LÂM (6 BƯU CỤC)')
    cell_tl.font = white_bold_font
    cell_tl.fill = navy_fill
    cell_tl.alignment = Alignment(horizontal='center', vertical='center')
    ws_cap.row_dimensions[5].height = 24
    for c in range(1, 11):
        ws_cap.cell(5, c).fill = navy_fill
        ws_cap.cell(5, c).border = thin_border

    # Rows 6-11: Tây Lâm data
    for idx, item in enumerate(tay_lam_cap):
        r = 6 + idx
        ws_cap.row_dimensions[r].height = 22
        vals = [
            item[0], item[1], item[2], item[3], item[4], item[5],
            item[6].format(r=r) if isinstance(item[6], str) else item[6],
            item[7].format(r=r) if isinstance(item[7], str) else item[7],
            item[8], item[9]
        ]
        for c, v in enumerate(vals, 1):
            cell = ws_cap.cell(r, c, v)
            cell.font = regular_font
            cell.border = thin_border
            if c in [1, 2, 4, 9]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif c in [3, 5, 6, 7, 8]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            if c == 1:
                cell.font = bold_font
            if c in [3, 8]:
                cell.number_format = '#,##0'
            elif c in [5, 6, 7]:
                cell.number_format = '0.0' if isinstance(v, (int, float)) or 'ROUND' in str(v) else '@'

    # Row 12: Section Header BẮC HÒA
    ws_cap.merge_cells('A12:J12')
    cell_bh = ws_cap.cell(12, 1, 'TỈNH BẮC HÒA (6 BƯU CỤC)')
    cell_bh.font = white_bold_font
    cell_bh.fill = slate_fill
    cell_bh.alignment = Alignment(horizontal='center', vertical='center')
    ws_cap.row_dimensions[12].height = 24
    for c in range(1, 11):
        ws_cap.cell(12, c).fill = slate_fill
        ws_cap.cell(12, c).border = thin_border

    # Rows 13-18: Bắc Hòa data
    for idx, item in enumerate(bac_hoa_cap):
        r = 13 + idx
        ws_cap.row_dimensions[r].height = 22
        vals = [
            item[0], item[1], item[2], item[3], item[4], item[5],
            item[6].format(r=r) if isinstance(item[6], str) else item[6],
            item[7].format(r=r) if isinstance(item[7], str) else item[7],
            item[8], item[9]
        ]
        for c, v in enumerate(vals, 1):
            cell = ws_cap.cell(r, c, v)
            cell.font = regular_font
            cell.border = thin_border
            if c in [1, 2, 4, 9]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif c in [3, 5, 6, 7, 8]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            if c == 1:
                cell.font = bold_font
            if c in [3, 8]:
                cell.number_format = '#,##0'
            elif c in [5, 6, 7]:
                cell.number_format = '0.0' if isinstance(v, (int, float)) or 'ROUND' in str(v) else '@'

    # Column dimensions for cap_hieu_chinh
    ws_cap.column_dimensions['A'].width = 16
    ws_cap.column_dimensions['B'].width = 14
    ws_cap.column_dimensions['C'].width = 15
    ws_cap.column_dimensions['D'].width = 12
    ws_cap.column_dimensions['E'].width = 13
    ws_cap.column_dimensions['F'].width = 13
    ws_cap.column_dimensions['G'].width = 18
    ws_cap.column_dimensions['H'].width = 18
    ws_cap.column_dimensions['I'].width = 24
    ws_cap.column_dimensions['J'].width = 65

    # ----------------------------------------------------
    # 2. UPGRADE SHEET chat_luong_lay
    # ----------------------------------------------------
    ws_lay = wb['chat_luong_lay']
    # Clear existing rows 4 to 25
    for r in range(4, 26):
        for c in range(1, 12):
            ws_lay.cell(r, c).value = None
            ws_lay.cell(r, c).fill = PatternFill(fill_type=None)
            ws_lay.cell(r, c).border = Border()
    for m in list(ws_lay.merged_cells.ranges):
        if m.min_row >= 4:
            ws_lay.unmerge_cells(str(m))

    headers_lay = ['Bưu Cục', 'Tỉnh', 'Trần Lấy TB/Ngày', 'Đơn Lấy TB 7 Ngày', '%LTC Gần Nhất', 'OPR Đúng Giờ', 'Đơn Chưa Xong Tồn', 'Đánh Giá Xu Hướng Chất Lượng Lấy', 'Nguy Cơ Vượt Trần Lấy 14 Ngày Tới']
    for c, h in enumerate(headers_lay, 1):
        cell = ws_lay.cell(4, c, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws_lay.row_dimensions[4].height = 28

    # Row 5: Section Header TÂY LÂM
    ws_lay.merge_cells('A5:I5')
    cell_tl_lay = ws_lay.cell(5, 1, 'TỈNH TÂY LÂM (6 BƯU CỤC)')
    cell_tl_lay.font = white_bold_font
    cell_tl_lay.fill = navy_fill
    cell_tl_lay.alignment = Alignment(horizontal='center', vertical='center')
    ws_lay.row_dimensions[5].height = 24
    for c in range(1, 10):
        ws_lay.cell(5, c).fill = navy_fill
        ws_lay.cell(5, c).border = thin_border

    # Rows 6-11: Tây Lâm lay data
    for idx, item in enumerate(tay_lam_lay):
        r = 6 + idx
        ws_lay.row_dimensions[r].height = 22
        for c, v in enumerate(item, 1):
            cell = ws_lay.cell(r, c, v)
            cell.font = regular_font
            cell.border = thin_border
            if c in [1, 2]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif c in [3, 4, 7]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if isinstance(v, (int, float)):
                    cell.number_format = '#,##0'
            elif c in [5, 6]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if isinstance(v, (int, float)):
                    cell.number_format = '0.0%'
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            if c == 1:
                cell.font = bold_font

    # Row 12: Section Header BẮC HÒA
    ws_lay.merge_cells('A12:I12')
    cell_bh_lay = ws_lay.cell(12, 1, 'TỈNH BẮC HÒA (6 BƯU CỤC)')
    cell_bh_lay.font = white_bold_font
    cell_bh_lay.fill = slate_fill
    cell_bh_lay.alignment = Alignment(horizontal='center', vertical='center')
    ws_lay.row_dimensions[12].height = 24
    for c in range(1, 10):
        ws_lay.cell(12, c).fill = slate_fill
        ws_lay.cell(12, c).border = thin_border

    # Rows 13-18: Bắc Hòa lay data
    for idx, item in enumerate(bac_hoa_lay):
        r = 13 + idx
        ws_lay.row_dimensions[r].height = 22
        for c, v in enumerate(item, 1):
            cell = ws_lay.cell(r, c, v)
            cell.font = regular_font
            cell.border = thin_border
            if c in [1, 2]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif c in [3, 4, 7]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if isinstance(v, (int, float)):
                    cell.number_format = '#,##0'
            elif c in [5, 6]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if isinstance(v, (int, float)):
                    cell.number_format = '0.0%'
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            if c == 1:
                cell.font = bold_font

    ws_lay.column_dimensions['A'].width = 16
    ws_lay.column_dimensions['B'].width = 14
    ws_lay.column_dimensions['C'].width = 16
    ws_lay.column_dimensions['D'].width = 16
    ws_lay.column_dimensions['E'].width = 14
    ws_lay.column_dimensions['F'].width = 14
    ws_lay.column_dimensions['G'].width = 16
    ws_lay.column_dimensions['H'].width = 32
    ws_lay.column_dimensions['I'].width = 45

    # ----------------------------------------------------
    # 3. UPDATE REFERENCES IN can_doi_tinh & canh_bao
    # ----------------------------------------------------
    # In can_doi_tinh:
    # Use VLOOKUP so it looks up by BC name in A5:H18 of cap_hieu_chinh
    ws_cd = wb['can_doi_tinh']
    for r in range(11, 23):
        ws_cd.cell(r, 4).value = f'=VLOOKUP(A{r}, cap_hieu_chinh!$A$5:$H$18, 8, FALSE)'

    # In canh_bao:
    # Lookup in A5:H18 of cap_hieu_chinh
    ws_cb = wb['canh_bao']
    for r in range(9, 177):
        ws_cb.cell(r, 5).value = f'=VLOOKUP(B{r}, cap_hieu_chinh!$A$5:$H$18, 8, FALSE)'

    wb.save(p)
    print('Updated successfully:', p)

