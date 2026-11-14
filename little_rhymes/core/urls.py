from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.page, {'slug': 'about'}, name='about'),
    path('privacy/', views.page, {'slug': 'privacy'}, name='privacy'),
    path('terms/', views.page, {'slug': 'terms'}, name='terms'),
    path('copyright/', views.page, {'slug': 'copyright'}, name='copyright'),
    path('resources/', views.page, {'slug': 'resources'}, name='resources'),
    path('faq/', views.faq, name='faq'),
    path('health/', views.health, name='health'),
    path('robots.txt', views.robots, name='robots'),
]
