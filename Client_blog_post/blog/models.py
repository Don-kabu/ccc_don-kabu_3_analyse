from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
	name = models.CharField(max_length=80, unique=True)
	slug = models.SlugField(max_length=90, unique=True, blank=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Article(models.Model):
	class Status(models.TextChoices):
		DRAFT = 'draft', 'Brouillon'
		PUBLISHED = 'published', 'Publie'

	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
	title = models.CharField(max_length=220)
	slug = models.SlugField(max_length=250, unique=True, blank=True)
	illustration_url = models.URLField(blank=True)
	intro = models.TextField()
	objectives = models.TextField(help_text='Une ligne par objectif pedagogique.')
	content = models.TextField(help_text='Corps principal de l article.')
	conclusion = models.TextField()
	reflection_questions = models.TextField(help_text='Une ligne par question de reflexion.')
	resources = models.TextField(help_text='Une ligne par ressource supplementaire.', blank=True)
	tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
	published_at = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title


class ReaderComment(models.Model):
	article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
	name = models.CharField(max_length=120, default='Lecteur')
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	is_approved = models.BooleanField(default=True)

	def __str__(self):
		return f'{self.name} - {self.article.title}'


class ArticleAnalytics(models.Model):
	article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name='analytics')
	total_reads = models.PositiveIntegerField(default=0)
	total_seconds_read = models.PositiveIntegerField(default=0)
	intro_seconds = models.PositiveIntegerField(default=0)
	objectives_seconds = models.PositiveIntegerField(default=0)
	content_seconds = models.PositiveIntegerField(default=0)
	conclusion_seconds = models.PositiveIntegerField(default=0)
	resources_seconds = models.PositiveIntegerField(default=0)
	updated_at = models.DateTimeField(auto_now=True)

	def section_score_pairs(self):
		return {
			'Introduction': self.intro_seconds,
			'Objectifs': self.objectives_seconds,
			'Contenu': self.content_seconds,
			'Conclusion': self.conclusion_seconds,
			'Ressources': self.resources_seconds,
		}

	def most_popular_section(self):
		pairs = self.section_score_pairs()
		return max(pairs, key=pairs.get)

	def average_time_per_read(self):
		if self.total_reads == 0:
			return 0
		return round(self.total_seconds_read / self.total_reads, 1)


class AnalyticsEvent(models.Model):
	article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='events')
	section = models.CharField(max_length=32)
	duration_seconds = models.PositiveIntegerField(default=0)
	session_id = models.CharField(max_length=80, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)


class ActionLog(models.Model):
	class DeliveryStatus(models.TextChoices):
		PENDING = 'pending', 'Pending'
		SENT = 'sent', 'Sent'
		FAILED = 'failed', 'Failed'

	action = models.CharField(max_length=80)
	actor_type = models.CharField(max_length=16, default='anonymous')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
	article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
	request_path = models.CharField(max_length=250, blank=True)
	request_method = models.CharField(max_length=10, blank=True)
	ip_address = models.CharField(max_length=64, blank=True)
	user_agent = models.CharField(max_length=255, blank=True)
	session_id = models.CharField(max_length=80, blank=True)
	payload = models.JSONField(default=dict, blank=True)
	delivery_status = models.CharField(max_length=12, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
	last_delivery_error = models.TextField(blank=True)
	delivery_attempts = models.PositiveIntegerField(default=0)
	sent_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.action} ({self.delivery_status})'
