from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_candidate),
    path('login/', views.login),
    path('refresh/', views.refresh_token),
    path('logout/', views.logout),
    path('get-system-users/', views.get_system_users, name='get_system_users'),
    path('get-hr-users/', views.get_hr_users, name='get_hr_users'),
    path('create-hr-account/', views.create_hr_account, name='create_hr_account'),
    path('change-password/', views.change_password, name='change_password'),
    path('me/', views.get_current_user, name='current_user'),
]   