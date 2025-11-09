from django import forms
from django.contrib.auth import get_user_model
from .models import BaiViet, BinhLuan, ToCao, Profile, TinNhan, NhomChat, TinNhanNhom

User = get_user_model()

class BaiVietForm(forms.ModelForm):
    class Meta:
        model = BaiViet
        exclude = ['slug', 'tac_gia', 'ngay_dang']  # Không cho chỉnh sửa các trường này
        widgets = {
            'noi_dung': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # 👈 Gán user vào instance
        super().__init__(*args, **kwargs)

        # ✅ Nếu user không phải admin thì ẩn trường 'nổi bật'
        if self.user and not self.user.groups.filter(name='Admin').exists():
            self.fields.pop('noi_bat', None)

        # ✅ Gán class CSS phù hợp cho các trường
        for name, field in self.fields.items():
            classes = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                classes = 'form-check-input'
            elif isinstance(field.widget, forms.ClearableFileInput):
                classes = 'form-control'
            field.widget.attrs['class'] = classes

class BinhLuanForm(forms.ModelForm):
    class Meta:
        model = BinhLuan
        fields = ['noi_dung']
        widgets = {
            'noi_dung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Viết bình luận...'
            }),
        }

class ToCaoForm(forms.ModelForm):
    class Meta:
        model = ToCao
        fields = ['ly_do']
        widgets = {
            'ly_do': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhập lý do bạn muốn tố cáo bài viết...'
            })
        }

from django import forms
from .models import TinNhan

class TinNhanForm(forms.ModelForm):
    class Meta:
        model = TinNhan
        fields = ['noi_dung', 'image', 'file']
        widgets = {
            "noi_dung": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nhập tin nhắn hoặc để trống nếu gửi ảnh/file..."
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        noi_dung = cleaned_data.get("noi_dung")
        image = cleaned_data.get("image")
        file = cleaned_data.get("file")

        # ✅ Nếu cả 3 đều trống => không hợp lệ
        if not noi_dung and not image and not file:
            raise forms.ValidationError("Bạn phải nhập nội dung hoặc gửi ảnh/file.")
        return cleaned_data

from .models import NhomChat, TinNhanNhom

class NhomChatForm(forms.ModelForm):
    class Meta:
        model = NhomChat
        fields = ["ten_nhom", "avatar", "thanh_vien"]  # 🆕 thêm avatar
        labels = {
            "ten_nhom": "Tên nhóm",
            "avatar": "Ảnh đại diện nhóm",   # 🆕 label đẹp hơn
            "thanh_vien": "Chọn thành viên",
        }
        widgets = {
            "thanh_vien": forms.CheckboxSelectMultiple,
        }

class TinNhanNhomForm(forms.ModelForm):
    class Meta:
        model = TinNhanNhom
        fields = ["noi_dung", 'image', 'file']
        widgets = {
            "noi_dung": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nhập tin nhắn hoặc để trống nếu gửi ảnh/file..."
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        noi_dung = cleaned_data.get("noi_dung")
        image = cleaned_data.get("image")
        file = cleaned_data.get("file")

        # ✅ Nếu cả 3 đều trống => không hợp lệ
        if not noi_dung and not image and not file:
            raise forms.ValidationError("Bạn phải nhập nội dung hoặc gửi ảnh/file.")
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio']