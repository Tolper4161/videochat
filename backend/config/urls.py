"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users.views import save_user, get_user_data, delete_user_by_id, update_username, update_password, user_login, user_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/register', save_user),
    path('api/users/login', user_login),
    path('api/users/logout', user_logout),
    path('api/users/delete/<user_id>', delete_user_by_id),
    path('api/users/account', get_user_data),
    path('api/users/edit/username', update_username),
    path('api/users/edit/password', update_password)
]
