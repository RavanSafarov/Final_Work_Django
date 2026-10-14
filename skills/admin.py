from django.contrib import admin
from .models import Category, SkillOffer, SessionRequest, Review, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(SkillOffer)
class SkillOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'level', 'format', 'status', 'created_at')
    list_filter = ('status', 'level', 'format', 'category')
    search_fields = ('title', 'description')


@admin.register(SessionRequest)
class SessionRequestAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'teacher', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('offer', 'user', 'rating', 'created_at')


admin.site.register(Favorite)