from django.urls import path
from . import views, api

app_name = 'analytics'

urlpatterns = [
    path('', views.api_docs, name='api_docs'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('explorateur/', views.explorateur, name='explorateur'),
    path('tendances/', views.tendances, name='tendances'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    # Author detail analytics
    path('auteurs/', views.auteur_list, name='auteur_list'),
    path('auteurs/<int:pk>/', views.auteur_detail, name='auteur_detail'),
    # User activity tab
    path('utilisateurs/', views.utilisateurs, name='utilisateurs'),
    # Legacy API endpoints – receive data from client app
    path('api/analytics/', views.receive_analytics, name='api_analytics'),
    path('api/action-log/', views.receive_action_log, name='api_action_log'),
    # Sync API endpoints – receive structured data from client
    path('api/sync/user/', api.sync_user, name='sync_user'),
    path('api/sync/tag/', api.sync_tag, name='sync_tag'),
    path('api/sync/article/', api.sync_article, name='sync_article'),
    path('api/sync/article-delete/', api.sync_article_delete, name='sync_article_delete'),
    path('api/sync/comment/', api.sync_comment, name='sync_comment'),
    path('api/sync/analytics/', api.sync_article_analytics, name='sync_analytics'),
    path('api/sync/event/', api.sync_analytics_event, name='sync_event'),
    path('api/sync/action-log/', api.sync_action_log, name='sync_action_log'),
    path('api/sync/full/', api.sync_full, name='sync_full'),
    path('accounts/logot/', views.logout_v, name='logout'),
]
