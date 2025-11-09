from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from bai_viet.models import BaiViet

# Tạo nhóm Admin nếu chưa có
admin_group, created = Group.objects.get_or_create(name='Admin')

# Lấy permission vừa tạo
content_type = ContentType.objects.get_for_model(BaiViet)
approve_perm = Permission.objects.get(codename='can_approve_post', content_type=content_type)

# Gán quyền vào nhóm Admin
admin_group.permissions.add(approve_perm)

print("✅ Gán quyền thành công cho nhóm Admin")
