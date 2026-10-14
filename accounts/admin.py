from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'avatar', 'bio', 'is_banned')}),
    )
    list_display = ('username', 'email', 'role', 'is_banned', 'is_staff')
    list_filter = ('role', 'is_banned', 'is_staff')