from django.contrib import admin

from .models import ActionLog, AnalyticsEvent, Article, ArticleAnalytics, ReaderComment, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'status', 'published_at', 'updated_at')
	list_filter = ('status', 'created_at', 'published_at')
	search_fields = ('title', 'intro', 'content')
	prepopulated_fields = {'slug': ('title',)}


@admin.register(ReaderComment)
class ReaderCommentAdmin(admin.ModelAdmin):
	list_display = ('article', 'name', 'is_approved', 'created_at')
	list_filter = ('is_approved', 'created_at')
	search_fields = ('name', 'message')


@admin.register(ArticleAnalytics)
class ArticleAnalyticsAdmin(admin.ModelAdmin):
	list_display = ('article', 'total_reads', 'total_seconds_read', 'updated_at')


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
	list_display = ('article', 'section', 'duration_seconds', 'session_id', 'created_at')
	list_filter = ('section', 'created_at')


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
	list_display = ('action', 'actor_type', 'user', 'article', 'delivery_status', 'delivery_attempts', 'created_at', 'sent_at')
	list_filter = ('delivery_status', 'actor_type', 'created_at')
	search_fields = ('action', 'request_path', 'ip_address', 'session_id')
