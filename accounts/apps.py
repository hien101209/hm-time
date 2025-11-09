from django.apps import AppConfig

class AccountsConfig(AppConfig):  # bạn có thể để tên gì cũng được, miễn không trùng
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'  # ❗ phải đúng với tên thư mục chứa app
