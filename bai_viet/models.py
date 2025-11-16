from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.cache import cache

User = get_user_model()

class BaiViet(models.Model):
    tieu_de = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    noi_dung = models.TextField()
    ngay_dang = models.DateTimeField(auto_now_add=True)
    tac_gia = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bai_viets"
    )
    danh_muc = models.CharField(max_length=100, blank=True)
    noi_bat = models.BooleanField(default=False)
    hinh_anh = models.ImageField(upload_to="bai_viet_images/", blank=True, null=True)

    # ✅ liên kết nhóm để áp dụng quyền trưởng nhóm
    nhom = models.ForeignKey(
        "NhomChat",
        on_delete=models.CASCADE,
        related_name="bai_viets",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.tieu_de

    def get_absolute_url(self):
        return reverse("chi_tiet_bai_viet", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.tieu_de)
        super().save(*args, **kwargs)
    def cache_key(self):
        return f"bai_{self.pk}"

    def get_cached(self):
        key = self.cache_key()
        data = cache.get(key)
        if not data:
            data = {
                "id": self.id,
                "tieu_de": self.tieu_de,
                "noi_dung": self.noi_dung,
                "ngay_dang": self.ngay_dang,
                "tac_gia": self.tac_gia_id,
                "slug": self.slug,
            }
            cache.set(key, data, 60)
        return data
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete("ds_bai_viet_home")
        cache.delete(f"bai_{self.pk}")
        cache.delete(f"baiviet_{self.slug}")
    class Meta:
        permissions = [
            ("can_approve_post", "Có thể phê duyệt bài viết"),
        ]

class MyModel(models.Model):
    image = models.ImageField(upload_to='images/')

class BinhLuan(models.Model):
    bai_viet = models.ForeignKey('BaiViet', on_delete=models.CASCADE, related_name='binh_luans')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    noi_dung = models.TextField()
    ngay_tao = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='phan_hoi')

    def __str__(self):
        return f"{self.user.username} - {self.ngay_tao.strftime('%d/%m/%Y %H:%M')}"

class ToCao(models.Model):
    bai_viet = models.ForeignKey(BaiViet, on_delete=models.CASCADE, related_name='to_cao')
    nguoi_to_cao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ly_do = models.TextField()
    ngay_to_cao = models.DateTimeField(auto_now_add=True)

    # ✅ Trạng thái xử lý
    da_xu_ly = models.BooleanField(default=False)

    class Meta:
        unique_together = ('bai_viet', 'nguoi_to_cao')

    def __str__(self):
        return f"Tố cáo bởi {self.nguoi_to_cao} - {self.bai_viet.tieu_de}"
    
class TinNhan(models.Model):
    nguoi_gui = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tin_gui"
    )
    nguoi_nhan = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tin_nhan"
    )
    noi_dung = models.TextField(null = True, blank=True)
    image = models.ImageField(upload_to='bai_viet_image/', blank=True, null=True)
    file = models.FileField(upload_to='bai_viet_file/', blank=True, null=True)
    thoi_gian = models.DateTimeField(auto_now_add=True)
    da_doc = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="chat_attachments/", null=True, blank=True)
    reply_to = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    # reactions: simple json field mapping user_id -> emoji
    reactions = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["thoi_gian"]

    def __str__(self):
        return f"{self.nguoi_gui} → {self.nguoi_nhan}: {self.noi_dung[:20]}"
    
class NhomChat(models.Model):
    ten_nhom = models.CharField(max_length=200)
    truong_nhom = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="nhom_truong"
    )
    thanh_vien = models.ManyToManyField(User, related_name="nhom_chats")
    ngay_tao = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to="nhom_avatars/", blank=True, null=True)  # 🆕 thêm avatar

    def __str__(self):
        return self.ten_nhom


class TinNhanNhom(models.Model):
    nhom = models.ForeignKey(
        NhomChat, on_delete=models.CASCADE, related_name="tin_nhans"  # sửa lại ở đây
    )
    nguoi_gui = models.ForeignKey(User, on_delete=models.CASCADE)
    noi_dung = models.TextField(null=True, blank=True)
    thoi_gian = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='bai_viet_image/', blank=True, null=True)
    file = models.FileField(upload_to='bai_viet_file/', blank=True, null=True)


    class Meta:
        ordering = ["thoi_gian"]

    def __str__(self):
        return f"[{self.nhom.ten_nhom}] {self.nguoi_gui.username}: {self.noi_dung[:20]}"
    
class KetBan(models.Model):
    CHO = "cho"
    CHAP_NHAN = "chap_nhan"
    TU_CHOI = "tu_choi"

    TRANG_THAI_CHOICES = [
        (CHO, "Đang chờ"),
        (CHAP_NHAN, "Đã chấp nhận"),
        (TU_CHOI, "Từ chối"),
    ]

    nguoi_gui = models.ForeignKey(User, related_name="loi_moi_gui", on_delete=models.CASCADE)
    nguoi_nhan = models.ForeignKey(User, related_name="loi_moi_nhan", on_delete=models.CASCADE)
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default=CHO)

    def __str__(self):
        return f"{self.nguoi_gui} → {self.nguoi_nhan} ({self.trang_thai})"


# Hàm lấy danh sách bạn bè
def get_ban_be(user):
    ketbans = KetBan.objects.filter(
        Q(nguoi_gui=user, trang_thai=KetBan.CHAP_NHAN) |
        Q(nguoi_nhan=user, trang_thai=KetBan.CHAP_NHAN)
    )
    ban_be_ids = []
    for kb in ketbans:
        if kb.nguoi_gui == user:
            ban_be_ids.append(kb.nguoi_nhan.id)
        else:
            ban_be_ids.append(kb.nguoi_gui.id)
    return User.objects.filter(id__in=ban_be_ids)

class NhomThanhVien(models.Model):
    nhom = models.ForeignKey(NhomChat, on_delete=models.CASCADE, related_name="ds_thanh_vien")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    ngay_tham_gia = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('nhom', 'user')

    def __str__(self):
        return f"{self.user.username} ({'Admin' if self.is_admin else 'Thành viên'}) - {self.nhom.ten_nhom}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"