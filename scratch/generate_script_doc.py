import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = docx.Document()

# Set standard margins
for section in doc.sections:
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

title = doc.add_paragraph()
r = title.add_run('KỊCH BẢN TRAO ĐỔI BÀI TEST CAPACITY 11.11 VỚI NHÀ TUYỂN DỤNG')
r.font.bold = True
r.font.size = Pt(16)
r.font.color.rgb = RGBColor(16, 44, 87)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

sub = doc.add_paragraph()
r_sub = sub.add_run('(Dành riêng cho Chị Thủy - Ngôn ngữ tự nhiên 100% người thật, vừa trao đổi vừa kể cách làm thực tế)')
r_sub.font.italic = True
r_sub.font.size = Pt(11)
r_sub.font.color.rgb = RGBColor(80, 80, 80)
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()

sections = [
    ("MỞ ĐẦU (Khoảng 10-15 giây - Bật slide, nói tự nhiên)",
"""Dạ chào anh và team, em vừa hoàn thành bài test Capacity đợt 11.11 này. Giờ em xin phép share màn hình rồi anh em mình cùng đi qua cách em bóc tách số liệu và tư duy xử lý nhé. Em có đúc kết ngắn gọn trong 5 slide để tiện trao đổi ạ."""),

    ("SLIDE 1: CÁCH EM BÓC TÁCH BỨC TRANH 2 TỈNH",
"""Đầu tiên khi nhận file đề bài, việc em làm trước là dựng mô hình hồi quy độ trễ luân chuyển từ Lag 0 đến Lag 3 để xem đơn tạo từ các sàn mất mấy ngày mới dội về bưu cục. Em lấy 35 ngày dữ liệu cũ ra đối soát thì thấy sai số tầm 2.4%, tức là độ khớp đạt cỡ 97.6% nên em khá yên tâm lấy số này chạy dự báo tiếp.

Khi chạy số ra ngày đỉnh 12/11 thì em thấy số liệu phân hóa rất rõ rệt luôn anh:

Bên Tây Lâm nhìn là thấy thiếu người thật sự. Bến Sỏi em soi vào bảng chấm công thì thấy rụng mất cả chục shipper, cap bưu cục teo từ hơn 1.500 xuống còn có 834 đơn. Lâm Viên 1 thì bị cắt 6 bạn sang bưu cục mới, Cầu Mây thì đơn dồn về đỉnh 1.565 đơn. Tổng cả tỉnh thiếu hụt gần 1.100 đơn.

Nhưng sang Bắc Hòa, lúc đầu nhìn tưởng thiếu người, mà đến khi em cộng tổng toàn tỉnh lại thì công suất lại dư ra được 42 đơn. Vấn đề của Bắc Hòa không phải là thiếu quân, mà bị nghẽn cục bộ ở hạ tầng và giờ xe: Phú Điền kho có 90m² mà xe 10h trưa mới tới; Hòa Lộc thì gãy chiều lấy; CK Bắc Hòa thì vướng hàng to cồng kềnh.

Nên ngay từ đầu em xác định luôn: 12 thời vụ em dồn toàn bộ cho Tây Lâm, còn Bắc Hòa em chốt 0 thời vụ, tuyệt đối không tuyển thêm người mà tập trung gỡ nút thắt hạ tầng."""),

    ("SLIDE 2: TƯ DUY PHÂN BỔ 12 THỜI VỤ VÀ ĐIỀU PHỐI NỘI BỘ",
"""Qua slide này là cách em tính toán và chia 12 bạn thời vụ:

Về sức tải thời vụ thì em chỉ dám tính tầm 70% so với anh em cũ thôi, rơi vào khoảng 42 đơn/bạn/ngày. Tại vì thời vụ mới vào lạ đường, tìm nhà lâu, mình không thể ép các bạn chạy như người cũ được. Với lại em cho các bạn nhận việc từ ngày 10/11 luôn, ngày đầu đi kẹp nách với shipper cứng để học tuyến, sang 11/11 mới bắt đầu chạy độc lập.

12 bạn này em chia cho 3 bưu cục thiếu người nhất Tây Lâm:
• Bến Sỏi nặng nhất em cho 6 bạn, kết hợp kéo thêm 2 anh em từ Gò Đào sang phụ, nâng cap bưu cục lên 1.210 đơn.
• Cầu Mây em cho 4 bạn gánh mấy tuyến lõi thị trấn.
• Lâm Viên 1 em bù 2 bạn để bù cho mấy bạn vừa chuyển đi.

Riêng Lâm Viên 2 bưu cục mới toe mở được 10 ngày thì em dứt khoát không nhét thời vụ vào, vì kho mới mà đưa người mới vào nữa là rối tung lên ngay. Em để Lâm Viên 1 gánh đỡ tuyến giáp ranh. Còn Gò Đào dư hơn 400 tải thì em biến thành bưu cục đệm gánh phụ 2 phường cho Bến Sỏi luôn."""),

    ("SLIDE 3: BÓC TÁCH 3 ĐIỂM NGHẼN BẮC HÒA (TẠI SAO THÊM NGƯỜI LÀ VÔ ÍCH)",
"""Sang Bắc Hòa, em đào sâu vào thì thấy nếu mình cứ đè ra tuyển thời vụ là coi như ném tiền qua cửa sổ:

Thứ nhất là Phú Điền: Kho có 90m² bé xíu, xe KTC lại đổi lịch về lúc 10h trưa. Sáng shipper lên ngồi chơi xơi nước, trưa xe về mới đổ đống ra chia hàng, vỡ sạch Ca 1. Sàn chật cứng không có chỗ cựa quậy thì bơm người vào chỉ có giẫm chân lên nhau. Chỗ này việc duy nhất phải làm là ép xe KTC về lại 6h30 sáng và thuê bãi đất ngoài sân dựng lều dã chiến chia hàng.

Thứ hai là CK Bắc Hòa: Trong file ghi công suất 2.600 nhưng đơn vị lại là energy. Em chia định mức 8 energy ra thì kho này chỉ giao được tầm 325 đơn thôi. Đơn về 405 đơn là vượt 24%, mà toàn tủ với nệm cồng kềnh. Hàng này shipper xe máy lắc đầu, có tuyển thời vụ xe máy cũng không giải quyết được gì, bắt buộc phải xin xe tải nhỏ hoặc ba gác tăng cường.

Thứ ba là Hòa Lộc: Bưu cục báo tỷ lệ đúng giờ cao, nhưng em nhìn kỹ lại thì chiều lấy đang vỡ trận, OPR tụt còn 63%, đơn lấy vượt trần 80%. Anh em bận đi giao nên bỏ bê chiều lấy của khách. Cái này em sẽ rút shipper giao xong sớm quay về gom hàng, và báo KTC cho xe tải ghé thẳng mấy shop lớn bốc hàng luôn, đỡ qua bưu cục trung chuyển."""),

    ("SLIDE 4: QUYẾT ĐỊNH ĐÒN BẨY SỐ 1 TRƯỚC NGÀY SALE",
"""Trong đề bài có hỏi nếu chỉ được chọn làm 1 việc duy nhất trước ngày 11/11 thì em làm gì?

Em chọn ngay việc: Đàm phán với KTC kéo chuyến xe Phú Điền từ 10h về lại 6h30 sáng!

Tại sao em ưu tiên việc này số 1?
Thứ nhất, việc điều quân nội bộ vùng mình chỉ cần một cuộc điện thoại là xử lý xong trong nửa ngày. Nhưng làm việc với KTC là việc liên phòng ban, bên đó họ còn phải sắp xếp tài xế và lộ trình xe, nếu mình không chốt sớm từ hôm nay thì đến ngày sale không bao giờ kịp trở tay.

Thứ hai, kéo được xe về sớm thì bưu cục giải phóng thêm được 343 đơn giao. Nó tương đương với việc em phải tuyển tới 7 bạn thời vụ mà công ty không tốn thêm một đồng chi phí nào. Hiệu quả đòn bẩy nó quá rõ ràng luôn anh."""),

    ("SLIDE 5: QUẢN TRỊ RỦI RO & DỮ LIỆU THỰC TẾ EM MUỐN XÁC NHẬN THÊM",
"""Ở Slide cuối cùng này, em muốn nhìn xa hơn một chút về góc độ rủi ro và những cái em muốn trao đổi thêm với team:

Lúc làm bài, em có tính thử độ nhạy: 3 ngày đỉnh 11, 12, 13/11 toàn vùng về tầm 45.000 đơn. Lúc này kho nào cũng chạy căng như dây đàn rồi. Chỉ cần sàn Shopee hay TikTok tung thêm cái voucher làm đơn tạo vọt nhẹ 10% thôi, là 10% của 45.000 đơn đó — tức 4.500 đơn phát sinh — nó đập thẳng vào phần quá tải luôn anh. Lượng đơn vượt của bưu cục sẽ tăng vọt thêm 66%, từ 6.800 lên hơn 11.000 đơn. Cho nên kế hoạch làm ra không thể tính khít 100% được mà lúc nào cũng phải có phương án san tải dự phòng.

Từ bài toán này, em rút ra 3 công thức nhẩm nhanh bỏ túi cho anh em điều hành:
• Một là: Số nhân sự cần thêm = Đơn vượt chia cho năng suất x 1.1 khi anh em tăng ca.
• Hai là: Sức tải 1 bạn thời vụ = 70% rider cứng x 1.1, tương đương tầm 42 đơn/bạn.
• Ba là: Đòn bẩy vận hành: 1 giờ xe về sớm = giải phóng thêm 343 đơn = tương đương tuyển 7 bạn thời vụ.

Và trên thực tế, ngồi xem file Excel thì không thể nào hiểu hết được hiện trường. Nếu bắt tay vào triển khai thật trên địa bàn, em sẽ cần kiểm tra lại ngay 5 điểm ở bảng bên phải:
1. Check xem danh sách shop lớn xả hàng ngày nào để đưa xe tải vào bốc thẳng từ shop về kho tổng, không để tràn về bưu cục;
2. Xuống CK Bắc Hòa xem thực tế hàng cồng kềnh chiếm bao nhiêu phần trăm để bố trí xe tải;
3. Rà soát lại toàn vùng xem ngoài Phú Điền ra còn bưu cục nào bị xe KTC dời giờ nữa không để xử lý dứt điểm;
4. Giục HR Vùng tiến độ tuyển bù 10 shipper cho Bến Sỏi, vì thời vụ chỉ đỡ được mấy ngày đỉnh, hết sale mà không có người chính thức là bưu cục lại rơi vào bể ngay;
5. Và theo dõi lại năng suất của Lâm Viên 2 vì anh em mới tách bưu cục chưa ổn định tuyến.

Đấy là toàn bộ cách em bóc tách và tư duy xử lý bài toán này. Em nghĩ làm Capacity thì số liệu mô hình là một chuyện, nhưng quan trọng nhất là phải bám thực tế kho bãi và con người dưới trạm. Anh với team xem qua thấy chỗ nào cần làm rõ hay có góc nhìn nào khác thì trao đổi với em nhé!""")
]

for heading, body in sections:
    h = doc.add_paragraph()
    r_h = h.add_run(heading)
    r_h.font.bold = True
    r_h.font.size = Pt(13)
    r_h.font.color.rgb = RGBColor(192, 0, 0) if 'SLIDE' in heading else RGBColor(0, 102, 204)
    
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)
    for line in body.split('\n'):
        r_b = p.add_run(line + '\n')
        r_b.font.size = Pt(11)
        r_b.font.name = 'Calibri'
        if line.startswith('•') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.'):
            r_b.font.bold = True

save_path = r'C:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\KICH_BAN_THUYET_TRINH_5_SLIDES.docx'
doc.save(save_path)
print('Updated 100% human conversational script successfully to:', save_path)
