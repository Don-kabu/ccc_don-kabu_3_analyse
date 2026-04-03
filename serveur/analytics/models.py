from django.db import models
from django.utils import timezone


class Teacher(models.Model):
    """Represents a teacher/author from the client application."""
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    client_user_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def __str__(self):
        return self.display_name


class Article(models.Model):
    """Mirror of client Article, enriched with server-side analytics."""
    client_article_id = models.PositiveIntegerField(unique=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=250, blank=True)
    category = models.CharField(max_length=80, blank=True)
    word_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ArticleMetrics(models.Model):
    """Aggregated analytics for one article."""
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name='metrics')
    total_reads = models.PositiveIntegerField(default=0)
    total_seconds_read = models.PositiveIntegerField(default=0)
    intro_seconds = models.PositiveIntegerField(default=0)
    objectives_seconds = models.PositiveIntegerField(default=0)
    content_seconds = models.PositiveIntegerField(default=0)
    conclusion_seconds = models.PositiveIntegerField(default=0)
    resources_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def avg_time_minutes(self):
        if self.total_reads == 0:
            return 0
        return round(self.total_seconds_read / self.total_reads / 60, 1)

    @property
    def visibility_percent(self):
        """Ratio of reading time vs estimated full reading time (word_count * 0.25s)."""
        expected = (self.article.word_count or 1200) * 0.25
        if expected == 0:
            return 0
        ratio = min(self.total_seconds_read / max(self.total_reads, 1) / expected, 1)
        return round(ratio * 100)

    def __str__(self):
        return f"Metrics – {self.article.title}"


class DailyReads(models.Model):
    """Daily read counts per article for trend charts."""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='daily_reads')
    date = models.DateField()
    reads = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('article', 'date')

    def __str__(self):
        return f"{self.article.title} – {self.date}: {self.reads}"


class RawEvent(models.Model):
    """Raw analytics/action events received from the client."""
    class EventType(models.TextChoices):
        ANALYTICS = 'analytics', 'Analytics'
        ACTION_LOG = 'action_log', 'Action Log'

    event_type = models.CharField(max_length=20, choices=EventType.choices)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='raw_events')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='raw_events')
    section = models.CharField(max_length=64, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    session_id = models.CharField(max_length=80, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=40, blank=True)
    action = models.CharField(max_length=80, blank=True)
    actor_type = models.CharField(max_length=20, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.event_type} – {self.received_at:%Y-%m-%d %H:%M}"
