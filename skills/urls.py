from django.urls import path
from . import views

urlpatterns = [
    path('', views.offer_list, name='offer_list'),
    path('popular/', views.popular_list, name='popular'),
    path('favorites/', views.favorite_list, name='favorites'),
    path('my-offers/', views.my_offers, name='my_offers'),
    path('my-requests/', views.my_requests, name='my_requests'),

    path('offer/create/', views.offer_create, name='offer_create'),
    path('offer/<int:pk>/', views.offer_detail, name='offer_detail'),
    path('offer/<int:pk>/edit/', views.offer_update, name='offer_update'),
    path('offer/<int:pk>/delete/', views.offer_delete, name='offer_delete'),
    path('offer/<int:offer_id>/request/', views.send_session_request, name='send_request'),
    path('offer/<int:offer_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('offer/<int:offer_id>/review/', views.review_create, name='review_create'),

    path('review/<int:pk>/edit/', views.review_update, name='review_update'),
    path('review/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('request/<int:request_id>/<str:action>/', views.handle_session_request, name='handle_request'),

    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:offer_id>/<str:action>/', views.moderate_offer, name='moderate_offer'),

    path('categories/', views.category_list, name='categories'),
    path('categories/manage/', views.category_manage, name='category_manage'),
    path('categories/<int:pk>/edit/', views.category_manage, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]