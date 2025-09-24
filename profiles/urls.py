from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Profile management
    path('', views.profile_detail, name='profile_detail'),
    path('edit/', views.profile_edit, name='profile_edit'),
    path('set-password/', views.set_inventory_password, name='set_inventory_password'),
]