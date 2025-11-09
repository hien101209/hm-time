from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView 
from django.urls import reverse_lazy
from django.contrib import messages

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            viewer_group, _ = Group.objects.get_or_create(name='Viewer')
            user.groups.add(viewer_group)
            messages.success(request, "✅ Đăng ký thành công! Hãy đăng nhập để tiếp tục.")
            return redirect('login')
        else:
            messages.error(request, "❌ Có lỗi xảy ra. Vui lòng kiểm tra lại biểu mẫu.")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True  # nếu đã login thì tự chuyển hướng

    def get_success_url(self):
        # Nếu đăng nhập thành công → chuyển tới trang profile
        if self.request.user.is_authenticated:
            return reverse_lazy('bai_viet:profile', kwargs={'user_id': self.request.user.id})
        return reverse_lazy('bai_viet:home')