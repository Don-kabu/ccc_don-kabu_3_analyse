from django.contrib import admin
from .models import Teacher, Article, ArticleMetrics, DailyReads, RawEvent


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
