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
from users.views import save_user, get_user_data_by_id, delete_user_by_id, set_new_email, set_new_password

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/registration', save_user),
    path('api/v1/users/delete/<user_id>', delete_user_by_id),
    path('api/v1/users/profile/<user_id>', get_user_data_by_id),
    path('api/v1/users/settings/password', set_new_password),
    path('api/v1/users/settings/email', set_new_email)
]
