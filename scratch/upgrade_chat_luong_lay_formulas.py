import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

paths = [
    r'c:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\BAO_CAO_CAPACITY_11.11_FINAL.xlsx',
    r'c:\Users\lap4all\Desktop\New folder\Capacity_Planning_Test\[GHN]_Capacity Planning_Test_T10.2026\BAO_CAO_CAPACITY_11.11_FINAL.xlsx'
]

# Load raw chat_luong_lay from lay_hang.xlsx
wb_lay_src = openpyxl.load_workbook(r'c:\Users\lap4all\Desktop\New folder\Capacity_Planning_Test\[GHN]_Capacity Planning_Test_T10.2026\lay_hang.xlsx', data_only=True)
ws_src_cl = wb_lay_src['chat_luong_lay']

for p in paths:
    print('Updating:', p)
    wb = openpyxl.load_workbook(p)
    
    # 1. Add sheet du_lieu_lay_hang if not exists
    if 'du_lieu_lay_hang' in wb.sheetnames:
        del wb['du_lieu_lay_hang']
    ws_raw = wb.create_sheet('du_lieu_lay_hang')
    
    # Copy all rows from lay_hang.xlsx chat_luong_lay
    for r in range(1, ws_src_cl.max_row + 1):
        for c in range(1, ws_src_cl.max_column + 1):
            val = ws_src_cl.cell(r, c).value
            ws_raw.cell(r, c, val)
            
    # Set headers styling
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    for c in range(1, ws_src_cl.max_column + 1):
        ws_raw.cell(1, c).fill = header_fill
        ws_raw.cell(1, c).font = header_font
        
    # 2. Update formulas in sheet chat_luong_lay
    ws_lay = wb['chat_luong_lay']
    
    # Rows for Tay Lam: 6 to 11
    # Rows for Bac Hoa: 13 to 18
    data_rows = list(range(6, 12)) + list(range(13, 19))
    
    for r in data_rows:
        bc_name = ws_lay.cell(r, 1).value
        if bc_name == 'Lâm Viên 2':
            ws_lay.cell(r, 3).value = 'Chưa đo'
            ws_lay.cell(r, 4).value = 0
            ws_lay.cell(r, 5).value = 'Chưa đo'
            ws_lay.cell(r, 6).value = 'Chưa đo'
            ws_lay.cell(r, 7).value = 0
            ws_lay.cell(r, 8).value = '⚪ CHƯA THIẾT LẬP TRẦN LẤY'
            ws_lay.cell(r, 9).value = 'Mới tách bưu cục từ 25/10, chưa có dữ liệu đo trần lấy.'
            continue
            
        # Col D: Đơn Lấy TB 7 Ngày (Lấy từ can_doi_tinh hoặc trung bình thực tế)
        # Col E: %LTC Gần Nhất = lay_tc / don_gan_lay
        ws_lay.cell(r, 5).value = f'=ROUND(SUMIF(du_lieu_lay_hang!$C$2:$C$400, A{r}, du_lieu_lay_hang!$E$2:$E$400) / SUMIF(du_lieu_lay_hang!$C$2:$C$400, A{r}, du_lieu_lay_hang!$D$2:$D$400), 3)'
        ws_lay.cell(r, 5).number_format = '0.0%'
        
        # Col F: OPR Đúng Giờ = opr_dung / opr_mau
        ws_lay.cell(r, 6).value = f'=ROUND(SUMIF(du_lieu_lay_hang!$C$2:$C$400, A{r}, du_lieu_lay_hang!$H$2:$H$400) / SUMIF(du_lieu_lay_hang!$C$2:$C$400, A{r}, du_lieu_lay_hang!$G$2:$G$400), 3)'
        ws_lay.cell(r, 6).number_format = '0.0%'
        
        # Col G: Đơn Chưa Xong Tồn = SUMIF don_chua_xong
        ws_lay.cell(r, 7).value = f'=SUMIF(du_lieu_lay_hang!$C$2:$C$400, A{r}, du_lieu_lay_hang!$F$2:$F$400)'
        ws_lay.cell(r, 7).number_format = '#,##0'
        
        # Col H: Đánh Giá Xu Hướng
        if bc_name == 'Hòa Lộc':
            ws_lay.cell(r, 8).value = f'="🔴 TỤT DỐC NGHIÊM TRỌNG (OPR sụt còn " & TEXT(F{r}, "0.0%") & ", %LTC còn " & TEXT(E{r}, "0.0%") & ")"'
        elif bc_name == 'Bến Sỏi':
            ws_lay.cell(r, 8).value = f'="🟢 CHẤT LƯỢNG GIỮ (OPR " & TEXT(F{r}, "0.0%") & "), NGUY CƠ THIẾU NGƯỜI"'
        else:
            ws_lay.cell(r, 8).value = f'="🟢 GIỮ ỔN ĐỊNH (OPR " & TEXT(F{r}, "0.0%") & ", LTC " & TEXT(E{r}, "0.0%") & ")"'
            
        # Col I: Nguy Cơ Vượt Trần (Dùng COUNTIFS và MAXIFS từ sheet canh_bao)
        if bc_name == 'Hòa Lộc':
            ws_lay.cell(r, 9).value = f'="VƯỢT TRẦN " & COUNTIFS(canh_bao!$B$10:$B$178, A{r}, canh_bao!$K$10:$K$178, ">0") & "/14 NGÀY (Peak " & TEXT(MAXIFS(canh_bao!$I$10:$I$178, canh_bao!$B$10:$B$178, A{r}), "#,##0") & " đơn, vượt 81%). Trưởng BC báo cáo sai lệch!"'
        elif bc_name == 'CK Bắc Hòa':
            ws_lay.cell(r, 9).value = f'="An toàn tuyệt đối, không vượt trần lấy (Peak " & TEXT(MAXIFS(canh_bao!$I$10:$I$178, canh_bao!$B$10:$B$178, A{r}), "#,##0") & "/200)."'
        else:
            ws_lay.cell(r, 9).value = f'="Vượt trần " & COUNTIFS(canh_bao!$B$10:$B$178, A{r}, canh_bao!$K$10:$K$178, ">0") & " ngày (Peak " & TEXT(MAXIFS(canh_bao!$I$10:$I$178, canh_bao!$B$10:$B$178, A{r}), "#,##0") & " đơn)."'
            
    wb.save(p)
    print('Saved:', p)

