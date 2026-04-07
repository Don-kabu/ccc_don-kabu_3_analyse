from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup_shortcut'),
    path('accounts/signup/', views.signup, name='signup'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/new/', views.article_create, name='article_create'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('articles/<slug:slug>/edit/', views.article_edit, name='article_edit'),
    path('articles/<slug:slug>/delete/', views.article_delete, name='article_delete'),
    path('dashboard/', views.author_dashboard, name='author_dashboard'),
    path('analytics/track/', views.track_analytics, name='track_analytics'),
    path('analytics/share/', views.track_share, name='track_share'),
    path("accounts/logout/", views.logout_view, name="logout"),
]
