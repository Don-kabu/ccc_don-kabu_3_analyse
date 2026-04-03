from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.api_docs, name='api_docs'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('explorateur/', views.explorateur, name='explorateur'),
    path('tendances/', views.tendances, name='tendances'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    # API endpoints – receive data from client app
    path('api/analytics/', views.receive_analytics, name='api_analytics'),
    path('api/action-log/', views.receive_action_log, name='api_action_log'),
]
