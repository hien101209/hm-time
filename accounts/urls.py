# accounts/urls.py

from django.urls import path
from .views import signup_view, CustomLoginView  # đảm bảo 2 view này tồn tại

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
]