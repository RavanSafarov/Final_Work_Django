from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('u/<str:username>/', views.public_profile_view, name='public_profile'),
    path('mentors/', views.mentor_list, name='mentors'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/ban/', views.toggle_ban, name='toggle_ban'),
    path('users/<int:user_id>/role/<str:role>/', views.set_role, name='set_role'),
]