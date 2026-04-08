from django.db import models
from django.utils import timezone


# ═══════════════════════════════════════════════════════════════════════════
# Legacy models (kept for backward-compatibility with existing RawEvent data)
# ═══════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════
# Client-synced models (tables prefixed with client_)
# All data is pushed from the client application via the sync API.
# ═══════════════════════════════════════════════════════════════════════════

class ClientUser(models.Model):
    """Mirror of the client auth_user table."""
    client_id = models.PositiveIntegerField(unique=True, help_text='PK in the client database')
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'client_user'

    @property
    def display_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def __str__(self):
        return self.display_name


class ClientTag(models.Model):
    """Mirror of the client blog_tag table."""
    client_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90)

    class Meta:
        db_table = 'client_tag'

    def __str__(self):
        return self.name


class ClientArticle(models.Model):
    """Mirror of the client blog_article table (full content)."""
    CATEGORY_LABELS = {
        'histoires_contes': 'Histoires courtes et contes',
        'defis_reflexion': 'Défis de réflexion',
        'decouverte_monde': 'Découverte du monde',
        'sciences_amusantes': 'Sciences amusantes',
        'maths_ludiques': 'Mathématiques ludiques',
        'apprentissage_mots': 'Apprentissage des mots',
        'activites_creatives': 'Activités créatives',
        'vie_quotidienne': 'Histoires de la vie quotidienne',
        'valeurs_comportements': 'Valeurs et comportements',
        'animaux_nature': 'Animaux et nature',
        'histoire_simplifiee': 'Histoire simplifiée',
        'initiation_numerique': 'Initiation au numérique',
        'jeux_role_imagination': 'Jeux de rôle et imagination',
        'jeux_educatifs': 'Jeux éducatifs interactifs',
        'comptines_chansons': 'Comptines et chansons',
        'metiers_reves': 'Métiers et rêves',
        'ecologie_environnement': 'Écologie et environnement',
        'emotions_bienetre': 'Émotions et bien-être',
        'langues_communication': 'Langues et communication',
        'histoires_interactives': 'Histoires interactives',
    }

    client_id = models.PositiveIntegerField(unique=True)
    author = models.ForeignKey(ClientUser, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=250, blank=True)
    category = models.CharField(max_length=40, blank=True)
    intro = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    content = models.TextField(blank=True)
    conclusion = models.TextField(blank=True)
    reflection_questions = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    illustration_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    enable_analytics = models.BooleanField(default=True)
    status = models.CharField(max_length=16, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    tags = models.ManyToManyField(ClientTag, blank=True, related_name='articles')

    class Meta:
        db_table = 'client_article'
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['category']),
        ]

    @property
    def category_label(self):
        return self.CATEGORY_LABELS.get(self.category, self.category or '—')

    @property
    def word_count(self):
        return len(self.content.split()) if self.content else 0

    def __str__(self):
        return self.title


class ClientReaderComment(models.Model):
    """Mirror of the client blog_readercomment table."""
    client_id = models.PositiveIntegerField(unique=True)
    article = models.ForeignKey(ClientArticle, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=120, default='Lecteur')
    email = models.EmailField(blank=True)
    message = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'client_readercomment'
        indexes = [
            models.Index(fields=['article', 'is_approved']),
        ]

    def __str__(self):
        return f'{self.name} - {self.article.title}'


class ClientArticleAnalytics(models.Model):
    """Mirror of the client blog_articleanalytics table."""
    client_id = models.PositiveIntegerField(unique=True)
    article = models.OneToOneField(ClientArticle, on_delete=models.CASCADE, related_name='analytics')
    total_reads = models.PositiveIntegerField(default=0)
    total_seconds_read = models.PositiveIntegerField(default=0)
    intro_seconds = models.PositiveIntegerField(default=0)
    objectives_seconds = models.PositiveIntegerField(default=0)
    content_seconds = models.PositiveIntegerField(default=0)
    conclusion_seconds = models.PositiveIntegerField(default=0)
    resources_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'client_articleanalytics'

    @property
    def avg_time_per_read(self):
        if self.total_reads == 0:
            return 0
        return round(self.total_seconds_read / self.total_reads, 1)

    @property
    def section_score_pairs(self):
        return {
            'Introduction': self.intro_seconds,
            'Objectifs': self.objectives_seconds,
            'Contenu': self.content_seconds,
            'Conclusion': self.conclusion_seconds,
            'Ressources': self.resources_seconds,
        }

    def __str__(self):
        return f"Analytics – {self.article.title}"


class ClientAnalyticsEvent(models.Model):
    """Mirror of the client blog_analyticsevent table."""
    client_id = models.PositiveIntegerField(unique=True)
    article = models.ForeignKey(ClientArticle, on_delete=models.CASCADE, related_name='analytics_events')
    section = models.CharField(max_length=32)
    duration_seconds = models.PositiveIntegerField(default=0)
    session_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'client_analyticsevent'

    def __str__(self):
        return f"{self.section} – {self.article.title}"


class ClientActionLog(models.Model):
    """Mirror of the client blog_actionlog table."""
    client_id = models.PositiveIntegerField(unique=True)
    action = models.CharField(max_length=80)
    actor_type = models.CharField(max_length=16, default='anonymous')
    user = models.ForeignKey(ClientUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
    article = models.ForeignKey(ClientArticle, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
    request_path = models.CharField(max_length=250, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    session_id = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'client_actionlog'
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['article', 'action']),
            models.Index(fields=['user', 'action']),
        ]

    def __str__(self):
        return f'{self.action} ({self.created_at})'
