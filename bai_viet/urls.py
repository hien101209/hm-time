# bai_viet/urls.py
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'bai_viet'

urlpatterns = [
    path('', views.home, name='home'),
    path('danh-sach/', views.danh_sach_bai_viet, name='danh_sach_bai_viet'),
    path('tao/', views.tao_bai_viet, name='tao_bai_viet'),
    path('sua/<int:pk>/', views.sua_bai_viet, name='sua_bai_viet'),
    path('xoa/<int:pk>/', views.xoa_bai_viet, name='xoa_bai_viet'),
    path('chi-tiet/<int:pk>/', views.chi_tiet_bai_viet, name='chi_tiet_bai_viet'),
    # 🆕 Thêm dòng này
    path('tim-kiem/', views.tim_kiem, name='tim_kiem'),
    path('phe-duyet/<int:bai_id>/', views.phe_duyet_bai, name='phe_duyet_bai'),
    path('duyet-noi-bat/<int:pk>/', views.duyet_noi_bat, name='duyet_noi_bat'),
    path('to-cao/<int:pk>/', views.to_cao_bai_viet, name='to_cao_bai_viet'),
    path('to-cao/', views.danh_sach_to_cao, name='danh_sach_to_cao'),
    path('chi-tiet-to-cao/<int:pk>/', views.chi_tiet_to_cao, name='chi_tiet_to_cao'),
    path('to-cao/<int:pk>/xu-ly/', views.danh_dau_xu_ly_tocao, name='danh_dau_xu_ly_tocao'),
    path('nhan-tin/<int:user_id>/', views.hop_thoai, name='hop_thoai'),
    path("nhom/", views.danh_sach_nhom, name="danh_sach_nhom"),
    path("nhom/tao/", views.tao_nhom, name="tao_nhom"),
    path("nhom/<int:nhom_id>/", views.chat_nhom, name="chat_nhom"),
    # Kết bạn
    path("ket-ban/gui/<int:user_id>/", views.gui_loi_moi_ket_ban, name="gui_loi_moi_ket_ban"),
    path("ket-ban/<int:ketban_id>/chap-nhan/", views.xu_ly_loi_moi, {"hanh_dong": "chapnhan"}, name="chap_nhan_ket_ban"),
    path("ket-ban/<int:ketban_id>/tu-choi/", views.xu_ly_loi_moi, {"hanh_dong": "tuchoi"}, name="tu_choi_ket_ban"),
    path("nhan-tin/", views.hop_thoai, name="hop_thoai"),  # vào trang hộp thoại tổng
    path("nhan-tin/<int:user_id>/", views.hop_thoai, name="hop_thoai_user"),  # chat với user
    path("nhom/<int:nhom_id>/roi/", views.roi_nhom, name="roi_nhom"),
    path("tim-kiem-ket-ban/", views.tim_kiem_ket_ban, name="tim_kiem_ket_ban"),
    path("ket-ban/<int:user_id>/", views.ket_ban, name="ket_ban"),
    path("unread_api/", views.unread_api, name="unread_api"),
    path("nhom/<int:nhom_id>/thanh-vien/", views.danh_sach_thanh_vien, name="danh_sach_thanh_vien"),
    path("ban-be/<int:user_id>/xoa/", views.xoa_ban_be, name="xoa_ban_be"),
    path("nhom/<int:nhom_id>/them-thanh-vien/", views.them_thanh_vien, name="them_thanh_vien"),
    path("nhom/<int:nhom_id>/kick/<int:user_id>/", views.kick_thanh_vien, name="kick_thanh_vien"),
    path("kiem-tra-admin/", views.check_admin_view, name="kiem_tra_admin"),
    path('doi-ten-nhom/<int:nhom_id>/', views.doi_ten_nhom, name='doi_ten_nhom'),
    path('nhom/<int:nhom_id>/toggle-quyen/<int:user_id>/', views.toggle_quyen_thanh_vien, name='toggle_quyen_thanh_vien'),
    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('accounts/', include('accounts.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)