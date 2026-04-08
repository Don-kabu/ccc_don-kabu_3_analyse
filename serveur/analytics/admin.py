from django.contrib import admin
from .models import (
    Teacher, Article, ArticleMetrics, DailyReads, RawEvent,
    ClientUser, ClientTag, ClientArticle, ClientReaderComment,
    ClientArticleAnalytics, ClientAnalyticsEvent, ClientActionLog,
)


# ═══════════════════════════════════════════════════════════════════════════
# Legacy models (server-side)
# ═══════════════════════════════════════════════════════════════════════════

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'username', 'email', 'client_user_id', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'word_count', 'published_at')
    list_filter = ('category',)
    search_fields = ('title', 'teacher__username')


@admin.register(ArticleMetrics)
class ArticleMetricsAdmin(admin.ModelAdmin):
    list_display = ('article', 'total_reads', 'avg_time_minutes', 'visibility_percent', 'updated_at')
    readonly_fields = ('avg_time_minutes', 'visibility_percent')


@admin.register(DailyReads)
class DailyReadsAdmin(admin.ModelAdmin):
    list_display = ('article', 'date', 'reads')
    list_filter = ('date',)


@admin.register(RawEvent)
class RawEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'teacher', 'article', 'section', 'duration_seconds', 'device_type', 'received_at')
    list_filter = ('event_type', 'device_type', 'browser')
    search_fields = ('teacher__username', 'article__title', 'action')


# ═══════════════════════════════════════════════════════════════════════════
# Synced client models
# ═══════════════════════════════════════════════════════════════════════════

@admin.register(ClientUser)
class ClientUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active',)


@admin.register(ClientTag)
class ClientTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'client_id')
    search_fields = ('name',)


@admin.register(ClientArticle)
class ClientArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'published_at', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'slug')
    raw_id_fields = ('author',)


@admin.register(ClientReaderComment)
class ClientReaderCommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'article', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('name', 'message')
    raw_id_fields = ('article', 'parent')


@admin.register(ClientArticleAnalytics)
class ClientArticleAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('article', 'total_reads', 'total_seconds_read', 'updated_at')
    raw_id_fields = ('article',)


@admin.register(ClientAnalyticsEvent)
class ClientAnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('article', 'section', 'duration_seconds', 'session_id', 'created_at')
    list_filter = ('section',)
    raw_id_fields = ('article',)


@admin.register(ClientActionLog)
class ClientActionLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor_type', 'user', 'article', 'ip_address', 'created_at')
    list_filter = ('action', 'actor_type')
    search_fields = ('action', 'ip_address', 'session_id')
    raw_id_fields = ('user', 'article')
