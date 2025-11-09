from django.shortcuts import render


def about_view(request):
    is_admin = request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()
    return render(request, 'about_me.html',{
        'is_admin': is_admin
    })
# Create your views here.
