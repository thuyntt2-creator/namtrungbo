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
r = title.add_run('KỊCH BẢN THUYẾT TRÌNH BẢO VỆ CAPACITY PLANNING MÙA SALE 11.11')
r.font.bold = True
r.font.size = Pt(16)
r.font.color.rgb = RGBColor(16, 44, 87)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

sub = doc.add_paragraph()
r_sub = sub.add_run('(Dành riêng cho Chị Thủy - Trợ lý Vận Hành Vùng | Đọc khớp 100% từng Slide PowerPoint TRINH_BAY_VONG_2_5_SLIDES.pptx)')
r_sub.font.italic = True
r_sub.font.size = Pt(11)
r_sub.font.color.rgb = RGBColor(80, 80, 80)
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()

slides_content = [
    ("LỜI MỞ ĐẦU (15 GIÂY - Bật màn hình chuẩn bị)", 
"""Kính thưa Ban Giám Đốc và Hội đồng tuyển dụng!
Em là Thủy, Trợ lý Vận Hành Vùng. Hôm nay, em xin phép được trình bày phương án Điều phối Năng lực & Quản trị Rủi ro cho đợt cao điểm đại lễ Sale 11.11 của 12 bưu cục vùng Ven Sông qua 5 slide ngắn gọn."""),

    ("SLIDE 1: BỨC TRANH TOÀN CẢNH & PHÂN HÓA NĂNG LỰC 2 TỈNH (08/11 – 21/11)",
"""Kính thưa Hội đồng, nhìn vào Slide 1 là Bức tranh toàn cảnh ngày đỉnh điểm 12/11. Dữ liệu chạy mô hình hồi quy độ trễ luân chuyển 4 ngày (độ chính xác đạt hơn 97.6%) cho thấy sự phân hóa hoàn toàn đối lập giữa 2 tỉnh:

• Thứ nhất, Tỉnh Tây Lâm – Báo động đỏ Thiếu sức giao thực sự: Ngày đỉnh đơn về 7.620 đơn, trong khi công suất thật chỉ có 6.529 đơn, toàn tỉnh thiếu hụt ròng tới 1.091 đơn (+16.7%). Nguyên nhân cốt lõi là khủng hoảng nhân sự: Bến Sỏi rụng mất 10 shipper làm cap sụt từ 1.542 xuống còn 834 đơn; Lâm Viên 1 tách 6 người sang Lâm Viên 2; và Cầu Mây quá tải đỉnh (1.565 đơn). Do đó, giải pháp bắt buộc là dồn trọn vẹn 100% nguồn lực 12 thời vụ cho Tây Lâm.

• Thứ hai, Tỉnh Bắc Hòa – Đủ tải tổng thể, nhưng nghẽn hạ tầng và giờ xe: Đơn về ngày đỉnh là 7.411 đơn so với công suất 7.453 đơn, tức là toàn tỉnh hoàn toàn đủ sức giao (thậm chí còn dư 42 đơn), không hề thiếu nhân sự. Tuy nhiên tỉnh bị nghẽn cục bộ tại 3 điểm: Phú Điền kẹt sàn 90m² và xe tải KTC về trễ 10h trưa; CK Bắc Hòa kẹt hàng cồng kềnh; và Hòa Lộc vỡ trận chiều lấy. Vì vậy, nguyên tắc của em là: Bắc Hòa tuyệt đối không bơm thêm thời vụ mà tập trung gỡ nút thắt giờ xe và bốc hàng thẳng tại shop."""),

    ("SLIDE 2: CHIẾN LƯỢC ĐIỀU PHỐI NGUỒN LỰC CAO ĐIỂM (10/11 – 15/11)",
"""Chuyển sang Slide 2, đây là Bảng phân bổ chi tiết 12 nhân sự thời vụ và điều phối liên bưu cục:

• Về phân bổ 12 thời vụ: Dồn 100% cho 3 bưu cục trọng điểm của Tây Lâm:
  1. Bến Sỏi nhận 6 bạn thời vụ (tăng thêm 252 đơn/ngày), kết hợp điều 2 shipper từ bưu cục Gò Đào sang hỗ trợ, nâng cap từ 834 lên 1.210 đơn.
  2. Cầu Mây nhận 4 bạn thời vụ (tăng thêm 168 đơn/ngày), nâng cap lên 1.292 đơn để giải tỏa lõi thị trấn.
  3. Lâm Viên 1 nhận 2 bạn thời vụ (tăng 84 đơn/ngày) để bù đắp việc tách bưu cục.

• Với các bưu cục còn lại: 
  - Lâm Viên 2 (0 thời vụ): Do bưu cục mới mở 10 ngày, nhân sự đang lạ đường, không nhồi thời vụ để tránh rối loạn; thay vào đó bưu cục mẹ Lâm Viên 1 sẽ gánh lại các tuyến giáp ranh.
  - Gò Đào: Đang rất dồi dào công suất (dư hơn 400 đơn), đóng vai trò bưu cục đệm nhận 2 phường giáp ranh của Bến Sỏi.

• Quy tắc huấn luyện thời vụ: Ngày 10/11 bắt buộc đi kèm 1-1 với rider cứng học tuyến và quy trình app (năng suất tính = 0 đơn). Từ 11/11 chạy độc lập các tuyến hàng nhỏ, áp định mức an toàn 70% năng suất chuẩn = 42 đơn/bạn/ngày."""),

    ("SLIDE 3: NÚT THẮT VẬN HÀNH NGOÀI PHẠM VI NHÂN SỰ & THẨM QUYỀN PHÊ DUYỆT",
"""Kính thưa Hội đồng, Slide 3 chỉ ra 3 điểm nghẽn tại Bắc Hòa mà 'Thêm người là vô ích', mỗi điểm nghẽn cần đúng cấp thẩm quyền xử lý:

1. Bưu cục Phú Điền (Kẹt sàn 90m² & xe KTC lùi về 10h): Sàn 90m² người đi lại còn khó, xe về 10h trưa làm bóp cap từ 1.409 xuống 1.066 đơn. Thêm người vào chỉ dẫm chân nhau. Giải pháp: Lệnh cho KTC trả chuyến xe đầu về 6h30 sáng để khôi phục lại 343 đơn công suất; đồng thời thuê bãi đất trống 90m² liền kề làm lều dã chiến phân loại. Cấp quyết định: Giám đốc Vùng làm việc với Điều phối KTC.

2. Bưu cục CK Bắc Hòa (Bẫy đơn vị 2.600 Energy): Thực tế 2.600 energy chia 8 energy/đơn chỉ ra 325 đơn thật. Đơn đỉnh 405 đơn là vượt 24.6% hàng cồng kềnh, thời vụ xe máy không thể chở được. Giải pháp: Tăng cường xe tải nhỏ/xe ba gác và Sales hẹn giờ giao với khách lớn. Cấp quyết định: Giám đốc Vùng + Khối Kinh Doanh.

3. Bưu cục Hòa Lộc (Báo động đỏ chiều lấy): Chiều giao đủ cap nhưng chiều lấy vỡ trận: đơn lấy vượt trần 81%, OPR rớt thảm hại còn 63.8%. Giải pháp: Chuyển 3-4 bạn giao xong sớm ca chiều sang hỗ trợ lấy, đồng thời yêu cầu KTC điều xe tải 1.5 tấn bốc thẳng tại 3 shop lớn (Direct Pickup). Cấp quyết định: Trưởng Bưu cục + Điều phối KTC.

• Giải pháp nhân sự dài hạn cho Bến Sỏi: Em kiến nghị HR Vùng bắt buộc phải duyệt tuyển bù khẩn cấp 10 shipper chính thức ngay trước sale, vì 6 thời vụ chỉ cứu cánh trong 5 ngày cao điểm, nếu không có người kế thừa thì bưu cục sẽ sập sau ngày 15/11."""),

    ("SLIDE 4: QUYẾT ĐỊNH ĐÒN BẨY QUAN TRỌNG NHẤT: ĐỔI GIỜ XE PHÚ ĐIỀN",
"""Kính thưa Hội đồng, ở Slide 4 là câu trả lời cho câu hỏi chiến lược: 'Nếu chỉ được chọn duy nhất 1 việc trước 11/11, em chọn việc gì?'

👉 Em chọn: KÉO CHUYẾN XE TẢI ĐẦU TIÊN CỦA PHÚ ĐIỀN TỪ 10H VỀ 6H30 SÁNG!

Bởi vì 2 lý do mang tính sống còn:
• Thứ nhất, Hiệu quả đòn bẩy khổng lồ (+343 đơn/ngày mà KHÔNG TỐN 1 ĐỒNG CHI PHÍ): Xe về lúc 6h30 giúp 20 rider có hàng chia chọn sớm, gán Ca 1 đạt >85%, chạy trọn vẹn 2 ca, khôi phục công suất từ 1.066 lên 1.409 đơn/ngày. Hiệu quả này tương đương với việc tuyển thêm 7 đến 8 bạn thời vụ!
• Thứ hai, Tính phụ thuộc bên ngoài và Lead time dài nhất: Điều động nội bộ vùng có thể quyết trong 1 buổi sáng, nhưng đổi biểu đồ xe KTC phụ thuộc vào Khối Vận tải bên ngoài, bắt buộc phải chốt lệnh trước 10/11 thì KTC mới kịp sắp xếp tài xế.

• Kịch bản dự phòng nếu KTC từ chối: Thuê ngay bãi đất trống liền kề 90m² dựng lều dã chiến + Cắt 2 tuyến giáp ranh sang Kênh Đào giao thay. Tuyệt đối không bơm thời vụ vào Phú Điền nếu xe vẫn về lúc 10h!"""),

    ("SLIDE 5: QUẢN TRỊ RỦI RO & HIỆU CHỈNH THỰC ĐỊA TRƯỚC NGÀY SALE 11.11",
"""Cuối cùng, Slide 5 là bài toán Quản trị rủi ro và Công thức phản ứng nhanh tại trận:

• Phân tích độ nhạy của thị trường: Mô hình rất nhạy ở vùng cận biên. Nếu sàn TMĐT tung voucher làm đơn tạo vượt thêm 10%, toàn vùng sẽ vượt thêm 4.500 đơn; nếu tăng 20% lượng vượt sẽ vọt lên 16.600 đơn trên toàn bộ 14 ngày.
• Công thức tính nhẩm nhanh tại hiện trường: 
  1. Số nhân sự cần = Đơn Vượt ÷ (Năng suất chuẩn × 1.1).
  2. Sức tải thời vụ = 42 đơn/bạn/ngày.
  3. Đòn bẩy vận hành: Cứ đổi sớm 1 giờ xe = giải phóng +343 đơn = tương đương 7 bạn thời vụ.
• 5 Loại dữ liệu thực địa cần bổ sung để tối ưu hóa: Cần nắm khoảng tin cậy danh sách shop lớn; tỷ trọng hàng cồng kềnh thực tế ở Bắc Hòa; giờ xe KTC thực tế từng bưu cục; tiến độ tuyển bù 10 shipper Bến Sỏi; và đo lại năng suất tại Lâm Viên 2.

LỜI KẾT (15 GIÂY):
Kính thưa Ban Giám Đốc, phương án của em giải quyết trúng 2 bài toán: Đúng người cho Tây Lâm và Đúng hạ tầng cho Bắc Hòa, bảo vệ vững chắc chỉ số ODR và tối ưu chi phí từng đồng cho công ty. Em xin chân thành cảm ơn và kính mời Ban Giám Đốc cùng Hội đồng đặt câu hỏi phản biện ạ!""")
]

for heading, body in slides_content:
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
        if line.startswith('•') or line.startswith('👉') or line.startswith('LỜI'):
            r_b.font.bold = True

save_path = r'C:\Users\lap4all\Desktop\BAI_NOP_CAPACITY_GHN\KICH_BAN_THUYET_TRINH_5_SLIDES.docx'
doc.save(save_path)
print('Saved successfully to:', save_path)

