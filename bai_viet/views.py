from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from datetime import date
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import BaiVietForm, BinhLuanForm
from .models import BaiViet, BinhLuan
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.text import slugify
from django.db.models import Count
from .models import ToCao
from .forms import ToCaoForm
from django.contrib.auth import get_user_model
from .models import TinNhan
from .forms import TinNhanForm
from django.db.models import Q
from .models import NhomChat, NhomThanhVien, BaiViet, TinNhanNhom, KetBan, get_ban_be
from .forms import NhomChatForm, TinNhanNhomForm
from .models import KetBan
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User, Group

def generate_unique_slug(title):
    slug = slugify(title)
    original_slug = slug
    counter = 1
    while BaiViet.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1
    return slug

@login_required
def tao_bai_viet(request):
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()
    if request.method == 'POST':
        form = BaiVietForm(request.POST, request.FILES)
        if form.is_valid():
            bai_viet = form.save(commit=False)

            # ✅ Đặt tác giả là người dùng hiện tại
            bai_viet.tac_gia = request.user

            # ✅ Tạo slug duy nhất từ tiêu đề
            bai_viet.slug = generate_unique_slug(bai_viet.tieu_de)

            # ✅ Nếu người tạo không phải admin thì không cho đánh dấu nổi bật
            if not request.user.is_staff:
                bai_viet.noi_bat = False

            bai_viet.save()
            messages.success(request, "✅ Bài viết đã được tạo thành công!")
            return redirect('bai_viet:danh_sach_bai_viet')
    else:
        form = BaiVietForm()

    return render(request, 'bai_viet/tao_bai_viet.html', {'form': form,'is_admin': is_admin})

@login_required
def sua_bai_viet(request, pk):
    bai_viet = get_object_or_404(BaiViet, pk=pk)
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    # ✅ Chỉ admin hoặc tác giả gốc mới có quyền sửa
    if not is_admin and bai_viet.tac_gia != request.user.username:
        return render(request, 'bai_viet/sua_bai_viet.html', {
            'form': None,
            'error_message': '⛔ Bạn không có quyền sửa bài viết này.',
            'bai_viet': bai_viet,
        })

    # ✅ Truyền user hiện tại vào form để xử lý quyền hiển thị trường nổi bật
    form = BaiVietForm(request.POST or None, request.FILES or None, instance=bai_viet, user=request.user)

    if request.method == 'POST' and form.is_valid():
        bai_viet_update = form.save(commit=False)

        # ✅ Không thay đổi tác giả
        bai_viet_update.tac_gia = bai_viet.tac_gia

        # ✅ Chỉ admin mới được giữ field nổi bật
        if not is_admin:
            bai_viet_update.noi_bat = bai_viet.noi_bat  # giữ nguyên trạng thái cũ

        # ✅ Tạo slug mới nếu tiêu đề bị thay đổi
        if bai_viet.tieu_de != bai_viet_update.tieu_de:
            bai_viet_update.slug = generate_unique_slug(bai_viet_update.tieu_de, exclude_pk=bai_viet.pk)

        bai_viet_update.save()
        messages.success(request, "✅ Bài viết đã được cập nhật.")
        return redirect('bai_viet:danh_sach_bai_viet')

    return render(request, 'bai_viet/sua_bai_viet.html', {
        'form': form,
        'bai_viet': bai_viet,
        'is_admin': is_admin
    })

@login_required
def xoa_bai_viet(request, pk):
    bai_viet = get_object_or_404(BaiViet, pk=pk)

    # ✅ Kiểm tra quyền admin
    is_admin = request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='Admin').exists()

    # ✅ Kiểm tra trưởng nhóm
    la_truong_nhom = (
        bai_viet.nhom and bai_viet.nhom.truong_nhom == request.user
    )

    # ✅ Kiểm tra tác giả
    la_tac_gia = (bai_viet.tac_gia == request.user)

    # Nếu không có quyền thì báo lỗi
    if not (is_admin or la_truong_nhom or la_tac_gia):
        return render(request, 'bai_viet/xoa_bai_viet.html', {
            'bai_viet': bai_viet,
            'error_message': '⛔ Bạn không có quyền xóa bài viết này.'
        })

    # Nếu xác nhận POST → xóa bài viết
    if request.method == 'POST':
        bai_viet.delete()
        return redirect('bai_viet:danh_sach_bai_viet')

    return render(request, 'bai_viet/xoa_bai_viet.html', {
        'bai_viet': bai_viet,
        'is_admin': is_admin,
        'la_truong_nhom': la_truong_nhom,
        'la_tac_gia': la_tac_gia,
    })

    
@login_required
def danh_sach_bai_viet(request):
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    # Tạo cache key theo toàn bộ URL
    cache_key = f"danh_sach_bai_viet:{request.get_full_path()}:{is_admin}"
    cached_page = cache.get(cache_key)

    if cached_page:
        print("⚡ CACHE HIT - danh sách bài viết")
        return cached_page

    print("💥 CACHE MISS - danh sách bài viết")

    if is_admin:
        danh_sach = BaiViet.objects.all()
    else:
        danh_sach = BaiViet.objects.filter(tac_gia=request.user)

    # --- Lọc ---
    tac_gia = request.GET.get('tac_gia', '').strip()
    danh_muc = request.GET.get('danh_muc', '').strip()
    ngay_dang = request.GET.get('ngay_dang', '').strip()

    if tac_gia:
        danh_sach = danh_sach.filter(tac_gia__icontains=tac_gia)
    if danh_muc:
        danh_sach = danh_sach.filter(danh_muc__icontains=danh_muc)
    if ngay_dang:
        danh_sach = danh_sach.filter(ngay_dang__date=ngay_dang)

    # --- Sắp xếp ---
    danh_sach = danh_sach.order_by('-ngay_dang')

    # --- Phân trang ---
    paginator = Paginator(danh_sach, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    response = render(request, 'bai_viet/danh_sach_bai_viet.html', {
        'danh_sach': page_obj,
        'is_admin': is_admin  
    })

    # Cache trong 30 giây
    cache.set(cache_key, response, 30)

    return response

from django.db.models import F

def chi_tiet_bai_viet(request, pk):

    # --- Không tăng view khi POST (ví dụ gửi bình luận)
    if request.method != 'POST':
        # 🔥 Cập nhật lượt xem an toàn (không bị đè khi có nhiều request)
        BaiViet.objects.filter(pk=pk).update(luot_xem=F('luot_xem') + 1)

    # --- Cache key
    cache_key = f"chi_tiet_bai_viet:{pk}"
    cached_page = cache.get(cache_key)

    # --- Dùng cache khi GET
    if cached_page and request.method != 'POST':
        print("⚡ CACHE HIT - chi tiết bài")
        return cached_page

    print("💥 CACHE MISS - chi tiết bài")

    # --- Load lại để lấy số view mới nhất
    bai_viet = get_object_or_404(BaiViet, pk=pk)
    binh_luans = bai_viet.binh_luans.filter(parent__isnull=True).order_by('-ngay_tao')

    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    form = BinhLuanForm()

    response = render(request, 'bai_viet/chi_tiet_bai_viet.html', {
        'bai_viet': bai_viet,
        'binh_luans': binh_luans,
        'form': form,
        'la_admin': is_admin,
        'is_admin': is_admin
    })

    # --- Cache trang trong 60 giây (GET)
    if request.method != 'POST':
        cache.set(cache_key, response, 60)

    return response

def home(request):
    page_number = request.GET.get("page", 1)

    # Cache theo trang để tránh tạo quá nhiều key
    cache_key = f"home:page:{page_number}"
    cached_page = cache.get(cache_key)

    if cached_page:
        print("⚡ CACHE HIT - home")
        return cached_page

    print("💥 CACHE MISS - home")

    # 🔥 TOP 6 bài viết có lượt xem cao nhất
    bai_viet_noi_bat = BaiViet.objects.order_by('-luot_xem')[:6]

    # 🔥 Các bài khác
    danh_sach_bai_viet = BaiViet.objects.exclude(
        id__in=bai_viet_noi_bat.values_list('id', flat=True)
    ).order_by('-ngay_dang')

    paginator = Paginator(danh_sach_bai_viet, 6)
    page_obj = paginator.get_page(page_number)

    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()
    can_approve = request.user.has_perm("bai_viet.can_approve_post")

    response = render(request, 'bai_viet/home.html', {
        'bai_viet_noi_bat': bai_viet_noi_bat,
        'bai_viets': page_obj,
        'today': date.today(),
        'can_approve': can_approve,
        'is_admin': is_admin
    })

    cache.set(cache_key, response, 15)  # 👉 giảm xuống 15 giây là tối ưu
    return response


def tim_kiem(request):
    cache_key = f"tim_kiem:{request.get_full_path()}"
    cached_page = cache.get(cache_key)

    if cached_page:
        print("⚡ CACHE HIT - tìm kiếm")
        return cached_page

    print("💥 CACHE MISS - tìm kiếm")

    query = request.GET.get('q', '').strip()
    tac_gia = request.GET.get('tac_gia', '').strip()
    danh_muc = request.GET.get('danh_muc', '').strip()
    ngay_dang = request.GET.get('ngay_dang', '').strip()
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    ket_qua = BaiViet.objects.all()

    if query:
        ket_qua = ket_qua.filter(tieu_de__icontains=query)
    if tac_gia:
        ket_qua = ket_qua.filter(tac_gia__icontains=tac_gia)
    if danh_muc:
        ket_qua = ket_qua.filter(danh_muc__icontains=danh_muc)
    if ngay_dang:
        ket_qua = ket_qua.filter(ngay_dang__date=ngay_dang)

    danh_mucs = BaiViet.objects.values_list('danh_muc', flat=True).distinct()
    tac_gias = BaiViet.objects.values_list('tac_gia', flat=True).distinct()

    response = render(request, 'bai_viet/tim_kiem.html', {
        'query': query,
        'tac_gia': tac_gia,
        'danh_muc': danh_muc,
        'ngay_dang': ngay_dang,
        'ket_qua': ket_qua,
        'today': date.today(),
        'danh_mucs': danh_mucs,
        'tac_gias': tac_gias,
        'is_admin': is_admin
    })

    cache.set(cache_key, response, 30)
    return response

def phe_duyet_bai(request, bai_id):
    bai_viet = get_object_or_404(BaiViet, id=bai_id)
    # ví dụ cập nhật trạng thái bài viết đã được phê duyệt
    bai_viet.noi_bat = True
    bai_viet.save()
    return redirect('bai_viet:danh_sach_bai_viet')  # hoặc redirect về đâu tùy bạn

@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Admin').exists())
def duyet_noi_bat(request, pk):
    bai_viet = get_object_or_404(BaiViet, pk=pk)
    bai_viet.noi_bat = True
    bai_viet.save()
    return redirect('bai_viet:danh_sach_bai_viet')

@login_required
def to_cao_bai_viet(request, pk):
    bai_viet = get_object_or_404(BaiViet, pk=pk)
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    if ToCao.objects.filter(bai_viet=bai_viet, nguoi_to_cao=request.user).exists():
        print(1)
        messages.warning(request, "⚠️ Bạn đã tố cáo bài viết này rồi.")
        return redirect('bai_viet:chi_tiet_bai_viet', pk=pk)

    if request.method == 'POST':
        form = ToCaoForm(request.POST)
        if form.is_valid():
            to_cao = form.save(commit=False)
            to_cao.bai_viet = bai_viet
            to_cao.nguoi_to_cao = request.user
            to_cao.save()
            messages.success(request, "✅ Cảm ơn bạn! Tố cáo đã được gửi.")
            print(to_cao)
            return redirect('bai_viet:chi_tiet_bai_viet', pk=pk)
    else:
        form = ToCaoForm()

    return render(request, 'bai_viet/to_cao_bai_viet.html', {
        'form': form,
        'bai_viet': bai_viet,
        'is_admin': is_admin
    })

@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Admin').exists())
def danh_sach_to_cao(request):
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    # Lấy danh sách các bài viết có ít nhất 1 tố cáo
    danh_sach = (
        BaiViet.objects
        .annotate(so_lan_to_cao=Count('to_cao'))
        .filter(so_lan_to_cao__gt=0)  # chỉ bài có tố cáo
        .order_by('-so_lan_to_cao', '-ngay_dang')  # sắp xếp: nhiều tố cáo → mới nhất
    )

    return render(request, 'bai_viet/danh_sach_to_cao.html', {
        'danh_sach': danh_sach,
        'is_admin': is_admin
    })

def chi_tiet_to_cao(request, pk):
    bai_viet = get_object_or_404(BaiViet, pk=pk)
    chua_xu_ly = bai_viet.to_cao.filter(da_xu_ly=False).order_by('-ngay_to_cao')
    da_xu_ly = bai_viet.to_cao.filter(da_xu_ly=True).order_by('-ngay_to_cao')
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    return render(request, 'bai_viet/chi_tiet_to_cao.html', {
        'bai_viet': bai_viet,
        'chua_xu_ly': chua_xu_ly,
        'da_xu_ly': da_xu_ly,
        'is_admin': is_admin
    })

@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Admin').exists())
def danh_dau_xu_ly_tocao(request, pk):
    to_cao = get_object_or_404(ToCao, pk=pk)
    to_cao.da_xu_ly = not to_cao.da_xu_ly  # Đổi trạng thái
    to_cao.save()
    messages.success(request, "✅ Đã cập nhật trạng thái tố cáo.")
    return redirect('bai_viet:chi_tiet_to_cao', pk=to_cao.bai_viet.pk)

User = get_user_model()

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

@login_required
def hop_thoai(request, user_id=None, nhom_id=None):
    print("check hop thoai")
    ban_be = get_ban_be(request.user)
    loi_moi_den = KetBan.objects.filter(nguoi_nhan=request.user, trang_thai=KetBan.CHO)
    loi_moi_di = KetBan.objects.filter(nguoi_gui=request.user, trang_thai=KetBan.CHO)
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    users = User.objects.exclude(id=request.user.id)

    # xử lý tìm kiếm người chưa kết bạn (dùng trong sidebar 'Tìm bạn')
    query = request.GET.get("q", "").strip()
    chua_ket_ban = []
    if query:
        chua_ket_ban = User.objects.filter(username__icontains=query).exclude(id=request.user.id) \
                         .exclude(id__in=get_ban_be(request.user).values_list('id', flat=True))

    # ============================
    # Gán unread_count cho từng bạn
    # ============================
    for u in ban_be:
        u.unread_count = TinNhan.objects.filter(
            nguoi_gui=u,
            nguoi_nhan=request.user,
            da_doc=False
        ).count()
        # is_online: ưu tiên profile.last_seen nếu có, else cache
        last_seen = getattr(u, "profile", None) and getattr(u.profile, "last_seen", None)
        if last_seen:
            u.is_online = (timezone.now() - last_seen) < timedelta(minutes=2)
        else:
            u.is_online = cache.get(f"online_user_{u.id}", False)

    # ============================
    # Gán unread_count cho từng nhóm
    # ============================
    nhoms = request.user.nhom_chats.all()
    for n in nhoms:
        n.unread_count = TinNhanNhom.objects.filter(
            nhom=n
        ).exclude(nguoi_gui=request.user).filter( # chỉ đếm tin chưa đọc: cần trường da_doc_group hoặc LastSeen per user -> tạm count all recent
            # nếu chưa có cơ chế per-user read for groups, ta count messages trong 24h để hiển thị
            thoi_gian__gte=timezone.now()-timedelta(days=7)
        ).count()
        # nhóm online: nếu bạn muốn hiển thị có người online -> check any member online
        n.is_online = any(cache.get(f"online_user_{m.id}", False) for m in n.thanh_vien.all())

    # Các biến chat hiện tại
    nguoi_nhan = None
    nhom = None
    tin_nhans = []
    form = None

    if user_id:
        nguoi_nhan = get_object_or_404(User, id=user_id)
        tin_nhans = TinNhan.objects.filter(
            Q(nguoi_gui=request.user, nguoi_nhan=nguoi_nhan) |
            Q(nguoi_gui=nguoi_nhan, nguoi_nhan=request.user)
        ).order_by("thoi_gian")

        # Mark as read
        TinNhan.objects.filter(
            nguoi_gui=nguoi_nhan,
            nguoi_nhan=request.user,
            da_doc=False
        ).update(da_doc=True)

        if request.method == "POST":
            form = TinNhanForm(request.POST, request.FILES)   # 👈 hỗ trợ file
            # print(form)
            print(form.data.get("noi_dung"))
            print(form.data.get(""))
            if form.data.get("noi_dung") in [None, ""]:
                print("Nội dung trống 2")
                mutable_data = form.data.copy()
                mutable_data["noi_dung"] = ""
    
                # Gán lại cho form
                form.data = mutable_data
            print(form.data.get("file") , 2)
            if form.is_valid():
                print(1)
                tn = form.save(commit=False)
                tn.nguoi_gui = request.user
                tn.nguoi_nhan = nguoi_nhan
                
                tn.save()
                return redirect("bai_viet:hop_thoai", user_id=user_id)
        else:
            form = TinNhanForm()

    elif nhom_id:
        nhom = get_object_or_404(NhomChat, id=nhom_id)
        # verify membership
        if request.user not in nhom.thanh_vien.all():
            messages.error(request, "Bạn không thuộc nhóm này.")
            return redirect("bai_viet:hop_thoai")
        tin_nhans = nhom.tin_nhans.all().order_by("thoi_gian")

        # TODO: mark group messages as read per-user (LastSeen) — cơ chế sau
        if request.method == "POST":
            form = TinNhanNhomForm(request.POST)
            if form.is_valid():
                tn = form.save(commit=False)
                tn.nhom = nhom
                tn.nguoi_gui = request.user
                tn.save()
                return redirect("bai_viet:hop_thoai", nhom_id=nhom_id)
        else:
            form = TinNhanNhomForm()

    return render(request, "bai_viet/hop_thoai.html", {
        "nguoi_nhan": nguoi_nhan,
        "nhom": nhom,
        "tin_nhans": tin_nhans,
        "form": form,
        "ban_be": ban_be,
        "loi_moi_den": loi_moi_den,
        "loi_moi_di": loi_moi_di,
        "search_results": None,
        "friends": ban_be,
        "sent_requests": [kb.nguoi_nhan for kb in loi_moi_di],
        "active_tab": "ban_be" if user_id else "nhom",
        "is_admin": is_admin,
        "chua_ket_ban": chua_ket_ban,
    })

@login_required
def tao_nhom(request):
    user_id = request.user.id
    ban_be = get_ban_be(request.user)   # ✅ chỉ lấy bạn bè thực sự (CHAP_NHAN)
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    if request.method == "POST":
        ten_nhom = request.POST.get("ten_nhom")
        thanh_vien_ids = request.POST.getlist("thanh_vien")
        nhom_truong_id = request.POST.get("nhom_truong")

        # ✅ tạo nhóm bằng NhomChat (thay vì Nhom)
        nhom = NhomChat.objects.create(
            ten_nhom=ten_nhom,
            truong_nhom=request.user
        )
        nhom.thanh_vien.add(request.user)  # luôn thêm người tạo nhóm

        # ✅ thêm bạn bè được chọn
        for uid in thanh_vien_ids:
            try:
                u = User.objects.get(id=uid)
                nhom.thanh_vien.add(u)
            except User.DoesNotExist:
                pass

        # ✅ set nhóm trưởng nếu có chọn trong form
        if nhom_truong_id:
            try:
                nhom.truong_nhom = User.objects.get(id=nhom_truong_id)
            except User.DoesNotExist:
                pass

        nhom.save()
        return redirect("bai_viet:chat_nhom", nhom_id=nhom.id)

    return render(request, "bai_viet/tao_nhom.html", {
        "ban_be": ban_be,
        'is_admin': is_admin,
    })

@login_required
def chat_nhom(request, nhom_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

    # ⛔ Chặn nếu user không trong nhóm
    if request.user not in nhom.thanh_vien.all():
        messages.error(request, "⛔ Bạn không thuộc nhóm này.")
        return redirect("home")

    tin_nhans = nhom.tin_nhans.all().order_by("thoi_gian")

    if request.method == "POST":
        form = TinNhanNhomForm(request.POST, request.FILES)  # 👈 hỗ trợ file
        if form.is_valid():
            tin = form.save(commit=False)
            tin.nhom = nhom
            tin.nguoi_gui = request.user
            print(tin.image)
            tin.save()
            return redirect("bai_viet:chat_nhom", nhom_id=nhom.id)
    else:
        form = TinNhanNhomForm()

    # 👉 Lấy lại danh sách bạn bè & lời mời (giống hop_thoai)
    ban_be = get_ban_be(request.user)
    loi_moi_den = KetBan.objects.filter(nguoi_nhan=request.user, trang_thai=KetBan.CHO)
    loi_moi_di = KetBan.objects.filter(nguoi_gui=request.user, trang_thai=KetBan.CHO)

    q = request.GET.get("q")
    search_results = None
    if q:
        search_results = User.objects.filter(
            username__icontains=q
        ).exclude(id=request.user.id)

    return render(request, "bai_viet/hop_thoai.html", {
        "nhom": nhom,
        "tin_nhans": tin_nhans,
        "form": form,
        "ban_be": ban_be,
        "loi_moi_den": loi_moi_den,
        "loi_moi_di": loi_moi_di,
        "search_results": search_results,
        "friends": ban_be,
        "sent_requests": [kb.nguoi_nhan for kb in loi_moi_di],
        "active_tab": "nhom",
        'is_admin': is_admin
    })

@login_required
def danh_sach_nhom(request):
    # tất cả nhóm user tham gia
    nhoms = request.user.nhom_chats.all().order_by("-ngay_tao")

    # nhóm do user làm trưởng nhóm
    nhoms_truong = nhoms.filter(truong_nhom=request.user)

    # nhóm user chỉ là thành viên
    nhoms_thanh_vien = nhoms.exclude(truong_nhom=request.user)

    return render(request, "bai_viet/danh_sach_nhom.html", {
        "nhoms": nhoms,
        "nhoms_truong": nhoms_truong,
        "nhoms_thanh_vien": nhoms_thanh_vien,
    })

# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import KetBan, User

@login_required
def gui_loi_moi_ket_ban(request, user_id):
    """Gửi lời mời kết bạn"""
    user = get_object_or_404(User, id=user_id)

    # 1️⃣ Không thể gửi cho chính mình
    if user == request.user:
        messages.warning(request, "⚠️ Bạn không thể gửi lời mời cho chính mình.")
        return redirect("bai_viet:hop_thoai")

    # 2️⃣ Kiểm tra xem đã là bạn bè chưa
    da_la_ban = KetBan.objects.filter(
        (
            Q(nguoi_gui=request.user, nguoi_nhan=user) |
            Q(nguoi_gui=user, nguoi_nhan=request.user)
        ),
        trang_thai=KetBan.CHAP_NHAN
    ).exists()
    if da_la_ban:
        messages.info(request, f"👬 Bạn và {user.username} đã là bạn bè.")
        return redirect("bai_viet:hop_thoai")

    # 3️⃣ Kiểm tra xem đã có lời mời chờ hoặc bị từ chối chưa
    loi_moi_ton_tai = KetBan.objects.filter(
        Q(nguoi_gui=request.user, nguoi_nhan=user) |
        Q(nguoi_gui=user, nguoi_nhan=request.user)
    ).exclude(trang_thai=KetBan.TU_CHOI).exists()

    if loi_moi_ton_tai:
        messages.warning(request, f"⚠️ Đã tồn tại lời mời kết bạn giữa bạn và {user.username}.")
        return redirect("bai_viet:hop_thoai")

    # 4️⃣ Tạo lời mời mới
    KetBan.objects.create(
        nguoi_gui=request.user,
        nguoi_nhan=user,
        trang_thai=KetBan.CHO
    )
    messages.success(request, f"✅ Đã gửi lời mời kết bạn đến {user.username}.")
    return redirect("bai_viet:hop_thoai")

@login_required
def xu_ly_loi_moi(request, ketban_id, hanh_dong):
    """Chấp nhận hoặc từ chối lời mời kết bạn"""
    ketban = get_object_or_404(KetBan, id=ketban_id, nguoi_nhan=request.user)

    if hanh_dong == "chapnhan":
        ketban.trang_thai = KetBan.CHAP_NHAN
        ketban.save()
        messages.success(request, f"✅ Bạn và {ketban.nguoi_gui.username} đã trở thành bạn bè.")
    
    elif hanh_dong == "tuchoi":
        ketban.trang_thai = KetBan.TU_CHOI
        ketban.save()
        messages.info(request, "❌ Bạn đã từ chối lời mời kết bạn.")

    return redirect("bai_viet:hop_thoai")

@login_required
def roi_nhom(request, nhom_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)

    if request.method != "POST":
        return redirect("bai_viet:chat_nhom", nhom_id=nhom.id)

    # Kiểm tra user có trong nhóm không
    if request.user not in nhom.thanh_vien.all():
        messages.warning(request, "⚠️ Bạn không thuộc nhóm này.")
        return redirect("bai_viet:chat_nhom", nhom_id=nhom.id)

    # Nếu là trưởng nhóm
    if nhom.truong_nhom == request.user:
        # Tìm thành viên khác để bổ nhiệm làm trưởng nhóm
        thanh_vien_moi = nhom.thanh_vien.exclude(id=request.user.id).first()

        if thanh_vien_moi:
            nhom.truong_nhom = thanh_vien_moi
            nhom.thanh_vien.remove(request.user)  # Xóa trưởng nhóm cũ ra khỏi nhóm
            nhom.save()
            messages.info(
                request,
                f"👑 Bạn đã rời nhóm. {thanh_vien_moi.username} đã được bổ nhiệm làm trưởng nhóm."
            )
        else:
            # Không còn thành viên → giải tán nhóm
            ten_nhom = nhom.ten_nhom  # 🔄 dùng đúng field
            nhom.delete()
            messages.info(
                request,
                f"🚪 Bạn đã rời nhóm '{ten_nhom}'. Nhóm không còn thành viên nên đã bị giải tán."
            )
            return redirect("bai_viet:hop_thoai")

    else:
        # Thành viên bình thường rời nhóm
        nhom.thanh_vien.remove(request.user)
        messages.success(request, f"🚪 Bạn đã rời khỏi nhóm '{nhom.ten_nhom}'.")

    return redirect("bai_viet:hop_thoai")

@login_required
def ket_ban(request, user_id):
    if request.method == "POST":
        ban = get_object_or_404(User, id=user_id)

        # nếu đã là bạn bè thì bỏ qua
        if request.user != ban:
            request.user.ban_be.add(ban)   # giả sử bạn có ManyToManyField ban_be
            ban.ban_be.add(request.user)  # thêm 2 chiều

    return redirect("bai_viet:hop_thoai")

@login_required
def unread_api(request):
    data = {"personal": {}, "groups": {}}

    # 🔹 Tin nhắn cá nhân chưa đọc
    for f in get_ban_be(request.user):
        c = TinNhan.objects.filter(
            nguoi_gui=f,
            nguoi_nhan=request.user,
            da_doc=False
        ).count()
        data["personal"][str(f.id)] = c

    # 🔹 Tin nhắn nhóm (tạm tính số tin trong 7 ngày gần đây chưa đọc)
    for g in request.user.nhom_chats.all():
        c = TinNhanNhom.objects.filter(
            nhom=g
        ).exclude(
            nguoi_gui=request.user
        ).filter(
            thoi_gian__gte=timezone.now() - timedelta(days=7)
        ).count()
        data["groups"][str(g.id)] = c

    return JsonResponse(data)

@login_required
def danh_sach_thanh_vien(request, nhom_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)
    thanh_vien = nhom.thanh_vien.all()

    # 👉 lấy danh sách bạn bè của user (chỉ bạn bè chưa có trong nhóm)
    ban_be = get_ban_be(request.user).exclude(id__in=thanh_vien.values_list("id", flat=True))

    return render(request, "bai_viet/danh_sach_thanh_vien.html", {
        "nhom": nhom,
        "thanh_vien": thanh_vien,
        "ban_be": ban_be,   # ✅ truyền xuống template
    })

@login_required
def xoa_ban_be(request, user_id):
    ban_be = get_object_or_404(User, id=user_id)
    # giả sử bạn lưu danh sách bạn bè trong ManyToManyField tên "ban_be"
    request.user.ban_be.remove(ban_be)
    messages.success(request, f"Đã xoá bạn bè: {ban_be.username}")
    return redirect("bai_viet:hop_thoai")

@login_required
def tim_kiem_ket_ban(request):
    query = request.GET.get("q", "").strip()
    ket_qua = []

    if query:
        ket_qua = User.objects.filter(username__icontains=query).exclude(id=request.user.id)

    return render(request, "bai_viet/tim_kiem_ket_ban.html", {
        "ket_qua": ket_qua,
        "query": query,
    })

@login_required
def them_thanh_vien(request, nhom_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)

    if request.user != nhom.truong_nhom:
        messages.error(request, "Chỉ trưởng nhóm mới có quyền thêm thành viên.")
        return redirect("bai_viet:danh_sach_thanh_vien", nhom_id=nhom.id)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        try:
            user = User.objects.get(id=user_id)

            if user in nhom.thanh_vien.all():
                messages.warning(request, f"{user.username} đã có trong nhóm.")
            else:
                nhom.thanh_vien.add(user)
                messages.success(request, f"Đã thêm {user.username} vào nhóm.")
        except User.DoesNotExist:
            messages.error(request, "Không tìm thấy người dùng.")

    return redirect("bai_viet:danh_sach_thanh_vien", nhom_id=nhom.id)

@login_required
def kick_thanh_vien(request, nhom_id, user_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)

    if request.user != nhom.truong_nhom:
        messages.error(request, "Chỉ trưởng nhóm mới có quyền xóa thành viên.")
        return redirect("bai_viet:danh_sach_thanh_vien", nhom_id=nhom.id)

    user = get_object_or_404(User, id=user_id)

    if user == nhom.truong_nhom:
        messages.error(request, "Không thể kick trưởng nhóm.")
    else:
        nhom.thanh_vien.remove(user)
        messages.success(request, f"Đã xóa {user.username} khỏi nhóm.")

    return redirect("bai_viet:danh_sach_thanh_vien", nhom_id=nhom.id)

@login_required
@require_POST
def upload_attachment(request):
    file = request.FILES.get("file")
    print(file)
    other_id = request.POST.get("other_id")
    nhom_id = request.POST.get("nhom_id")
    if other_id:
        other = get_object_or_404(User, id=other_id)
        tn = TinNhan.objects.create(nguoi_gui=request.user, nguoi_nhan=other, attachment=file)
    elif nhom_id:
        nhom = get_object_or_404(NhomChat, id=nhom_id)
        tn = TinNhan.objects.create(nguoi_gui=request.user, nhom=nhom, attachment=file)
    else:
        return JsonResponse({"error":"missing target"}, status=400)

    return JsonResponse({
        "id": tn.id,
        "attachment_url": tn.attachment.url,
        "thoi_gian": tn.thoi_gian.isoformat(),
    })

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def check_admin_view(request):
    user = request.user
    data = {
        "username": user.username,
        "is_superuser": user.is_superuser,  # True nếu là superadmin
        "is_staff": user.is_staff,          # True nếu có quyền vào /admin
    }
    return JsonResponse(data)

@login_required
def doi_ten_nhom(request, nhom_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)
    if request.user != nhom.truong_nhom:
        return JsonResponse({"error": "Không có quyền"}, status=403)
    if request.method == "POST":
        ten_moi = request.POST.get("ten_moi", "").strip()
        if ten_moi:
            nhom.ten_nhom = ten_moi
            nhom.save()
            return JsonResponse({"success": True, "new_name": ten_moi})
    return JsonResponse({"error": "Tên không hợp lệ"}, status=400)

@login_required
def toggle_quyen_thanh_vien(request, nhom_id, user_id):
    nhom = get_object_or_404(NhomChat, id=nhom_id)
    if request.user != nhom.truong_nhom:
        return HttpResponseForbidden()
    print(nhom.truong_nhom)
    user = get_object_or_404(User, id=user_id)
    # thanhvien, created = NhomThanhVien.objects.get_or_create(nhom=nhom, user=user)
    nhom.truong_nhom = user
    nhom.save()
    print(nhom.truong_nhom)


    # thanhvien.is_admin = not thanhvien.is_admin
    # thanhvien.save()

    # if thanhvien.is_admin:
    #     messages.success(request, f"✅ Đã nâng {user.username} lên quản trị viên!")
    # else:
    #     messages.warning(request, f"⬇️ Đã hạ quyền {user.username}.")
    
    return redirect("bai_viet:danh_sach_thanh_vien", nhom.id)

@login_required
def profile_view(request, user_id=None):
    """
    Hiển thị trang hồ sơ người dùng.
    - Chỉ chủ nhân tài khoản có thể chỉnh sửa thông tin.
    - Người khác chỉ được xem.
    """

    # Lấy user được xem
    user_obj = get_object_or_404(User, id=user_id) if user_id else request.user

    # Tạo profile nếu chưa có
    profile, _ = Profile.objects.get_or_create(user=user_obj)

    # Kiểm tra chủ sở hữu
    is_own_profile = (user_obj == request.user)

    # Form chỉ hiển thị khi là chủ sở hữu
    user_form = UserUpdateForm(instance=user_obj) if is_own_profile else None
    profile_form = ProfileUpdateForm(instance=profile) if is_own_profile else None

    # Xử lý POST (chỉ chủ nhân mới được phép)
    if request.method == 'POST' and is_own_profile:
        if 'update_image' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "📸 Ảnh đại diện đã được cập nhật!")
                return redirect('bai_viet:profile', user_id=user_obj.id)

        elif 'update_info' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=user_obj)
            profile_form = ProfileUpdateForm(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "✅ Cập nhật thông tin thành công!")
                return redirect('bai_viet:profile', user_id=user_obj.id)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_obj': user_obj,
        'is_own_profile': is_own_profile,
    }

    return render(request, 'bai_viet/profile.html', context)

def chap_nhan_loi_moi(request, ketban_id):
    ketban = get_object_or_404(KetBan, id=ketban_id, nguoi_nhan=request.user)
    ketban.trang_thai = KetBan.CHAP_NHAN
    ketban.save()
    messages.success(request, "🎉 Hai bạn đã trở thành bạn bè!")
    return redirect("ten_trang_nao_do")
