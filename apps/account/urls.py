from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

app_name = 'account'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('address/', views.address_list, name='address'),
    path('address/add/', views.address_add, name='address_add'),
    path('address/edit/<int:pk>/', views.address_edit, name='address_edit'),
    path('address/delete/<int:pk>/', views.address_delete, name='address_delete'),

    ]