import json

with open(r'C:\Users\lap4all\Desktop\New folder\data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Let's inspect all 20 AM names from cocau
ams_20 = [
    'Trần Nguyễn Huyền Trang', 'Nguyễn Thị Tuyết Thơ', 'Lê Hồng Phong',
    'Nguyễn Thanh Long', 'Nguyễn Lê Nguyên Vũ', 'Nguyễn Duy Long',
    'Hồng Bích Nga', 'Thái Thị Thanh Thư', 'Phan Đình Duy',
    'Lê Thanh Nhựt', 'Nguyễn Hoàng Phi', 'Lê Văn Trường',
    'Cao Thị Thanh Thủy', 'Phan Nguyễn Yến Nhi', 'Huỳnh Thị Kim Chi',
    'Nguyễn Đỗ Minh Nghĩa', 'Nguyễn Ngọc Khánh', 'Trần Thị Nhung',
    'Lê Minh Lợi', 'Huỳnh Trúc Duyên'
]
print("Standard 20 AMs count:", len(ams_20))

