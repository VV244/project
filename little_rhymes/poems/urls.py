from django.urls import path
from . import views, api

app_name = 'poems'
urlpatterns = [
    path('poems/', views.listing, name='list'),
    path('poems/<slug:slug>/', views.detail, name='detail'),
    path('classes/', views.directory, {'kind': 'classes'}, name='classes'),
    path('classes/<slug:slug>/', views.listing, {'kind': 'class'}, name='class'),
    path('languages/', views.directory, {'kind': 'languages'}, name='languages'),
    path('languages/<slug:slug>/', views.listing, {'kind': 'language'}, name='language'),
    path('categories/', views.directory, {'kind': 'categories'}, name='categories'),
    path('categories/<slug:slug>/', views.listing, {'kind': 'category'}, name='category'),
    path('favorites/', views.favorites, name='favorites'),
    path('staff/poems/<int:pk>/preview/', views.preview, name='preview'),
    path('api/poems/', api.PoemListAPI.as_view(), name='api-list'),
    path('api/poems/<slug:slug>/', api.PoemDetailAPI.as_view(), name='api-detail'),
]
