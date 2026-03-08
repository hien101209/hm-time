import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()

from django.contrib.auth.models import User
from bai_viet.models import BaiViet, NhomChat

# Tạo user mẫu nếu chưa có
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_user('admin', 'admin@example.com', 'password123')
    user.is_staff = True
    user.is_superuser = True
    user.save()
else:
    user = User.objects.get(username='admin')

# Tạo nhóm mẫu nếu cần
if not NhomChat.objects.filter(ten_nhom='Nhóm Chung').exists():
    nhom = NhomChat.objects.create(ten_nhom='Nhóm Chung', truong_nhom=user)
    nhom.thanh_vien.add(user)
else:
    nhom = NhomChat.objects.get(ten_nhom='Nhóm Chung')

# Tạo bài viết mẫu
sample_posts = [
    {
        'tieu_de': 'Chào mừng đến với trang web của chúng tôi',
        'noi_dung': '''Chào mừng bạn đến với trang web của chúng tôi! Đây là nơi bạn có thể tìm thấy nhiều thông tin hữu ích và thú vị.

Chúng tôi cung cấp các bài viết về nhiều chủ đề khác nhau, từ công nghệ, giáo dục đến giải trí. Hãy khám phá và tận hưởng!''',
        'danh_muc': 'Giới thiệu',
        'noi_bat': True,
    },
    {
        'tieu_de': 'Hướng dẫn sử dụng Django',
        'noi_dung': '''Django là một framework web mạnh mẽ được viết bằng Python. Trong bài viết này, chúng ta sẽ tìm hiểu cách sử dụng Django để xây dựng ứng dụng web.

Đầu tiên, bạn cần cài đặt Django:
pip install django

Sau đó tạo project:
django-admin startproject myproject

Và chạy server:
python manage.py runserver''',
        'danh_muc': 'Công nghệ',
        'noi_bat': False,
    },
    {
        'tieu_de': 'Mẹo học tập hiệu quả',
        'noi_dung': '''Học tập hiệu quả là chìa khóa để thành công. Dưới đây là một số mẹo giúp bạn học tập tốt hơn:

1. Lập kế hoạch học tập hàng ngày
2. Tạo môi trường học tập yên tĩnh
3. Kết hợp giữa lý thuyết và thực hành
4. Nghỉ ngơi hợp lý
5. Ôn tập thường xuyên

Áp dụng những mẹo này sẽ giúp bạn cải thiện kết quả học tập đáng kể.''',
        'danh_muc': 'Giáo dục',
        'noi_bat': True,
    },
    {
        'tieu_de': 'Công thức nấu ăn đơn giản',
        'noi_dung': '''Bạn đang tìm kiếm những công thức nấu ăn đơn giản cho bữa tối gia đình? Hãy thử công thức salad rau củ tươi này:

Nguyên liệu:
- 2 quả cà chua
- 1 quả dưa leo
- 1 bó rau xà lách
- 1 củ hành tây
- Dầu olive, giấm, muối

Cách làm:
1. Rửa sạch tất cả rau củ
2. Cắt cà chua, dưa leo thành miếng nhỏ
3. Thái hành tây mỏng
4. Trộn rau xà lách với các nguyên liệu
5. Thêm dầu olive, giấm và muối theo khẩu vị

Thưởng thức ngay!''',
        'danh_muc': 'Ẩm thực',
        'noi_bat': False,
    },
    {
        'tieu_de': 'Lợi ích của thể thao',
        'noi_dung': '''Thể thao không chỉ giúp bạn có sức khỏe tốt mà còn mang lại nhiều lợi ích khác:

- Cải thiện sức khỏe tim mạch
- Giảm stress và cải thiện tâm trạng
- Tăng cường sự tự tin
- Phát triển kỹ năng xã hội
- Giúp duy trì cân nặng hợp lý

Hãy bắt đầu tập thể thao ngay hôm nay để có cuộc sống khỏe mạnh hơn!''',
        'danh_muc': 'Sức khỏe',
        'noi_bat': True,
    }
]

for post_data in sample_posts:
    if not BaiViet.objects.filter(tieu_de=post_data['tieu_de']).exists():
        BaiViet.objects.create(
            tieu_de=post_data['tieu_de'],
            noi_dung=post_data['noi_dung'],
            tac_gia=user,
            danh_muc=post_data['danh_muc'],
            noi_bat=post_data['noi_bat'],
            nhom=nhom
        )
        print(f"Đã tạo bài viết: {post_data['tieu_de']}")
    else:
        print(f"Bài viết đã tồn tại: {post_data['tieu_de']}")

print("Hoàn thành tạo dữ liệu mẫu!")