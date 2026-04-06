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

	class Category(models.TextChoices):
		HISTOIRES_CONTES         = 'histoires_contes',         'Histoires courtes et contes'
		DEFIS_REFLEXION          = 'defis_reflexion',          'Défis de réflexion'
		DECOUVERTE_MONDE         = 'decouverte_monde',         'Découverte du monde'
		SCIENCES_AMUSANTES       = 'sciences_amusantes',       'Sciences amusantes'
		MATHS_LUDIQUES           = 'maths_ludiques',           'Mathématiques ludiques'
		APPRENTISSAGE_MOTS       = 'apprentissage_mots',       'Apprentissage des mots'
		ACTIVITES_CREATIVES      = 'activites_creatives',      'Activités créatives'
		VIE_QUOTIDIENNE          = 'vie_quotidienne',          'Histoires de la vie quotidienne'
		VALEURS_COMPORTEMENTS    = 'valeurs_comportements',    'Valeurs et comportements'
		ANIMAUX_NATURE           = 'animaux_nature',           'Animaux et nature'
		HISTOIRE_SIMPLIFIEE      = 'histoire_simplifiee',      'Histoire simplifiée'
		INITIATION_NUMERIQUE     = 'initiation_numerique',     'Initiation au numérique'
		JEUX_ROLE_IMAGINATION    = 'jeux_role_imagination',    'Jeux de rôle et imagination'
		JEUX_EDUCATIFS           = 'jeux_educatifs',           'Jeux éducatifs interactifs'
		COMPTINES_CHANSONS       = 'comptines_chansons',       'Comptines et chansons'
		METIERS_REVES            = 'metiers_reves',            'Métiers et rêves'
		ECOLOGIE_ENVIRONNEMENT   = 'ecologie_environnement',   'Écologie et environnement'
		EMOTIONS_BIENETRE        = 'emotions_bienetre',        'Émotions et bien-être'
		LANGUES_COMMUNICATION    = 'langues_communication',    'Langues et communication'
		HISTOIRES_INTERACTIVES   = 'histoires_interactives',   'Histoires interactives'

	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
	title = models.CharField(max_length=220)
	slug = models.SlugField(max_length=250, unique=True, blank=True)
	category = models.CharField(
		max_length=40,
		choices=Category.choices,
		blank=True,
		db_index=True,
		help_text='Catégorie principale de l\'article.',
	)
	illustration_url = models.URLField(blank=True)
	illustration_upload = models.FileField(upload_to='articles/images/', blank=True, null=True)
	video_url = models.URLField(blank=True)
	video_upload = models.FileField(upload_to='articles/videos/', blank=True, null=True)
	audio_url = models.URLField(blank=True)
	audio_upload = models.FileField(upload_to='articles/audio/', blank=True, null=True)
	enable_analytics = models.BooleanField(default=True)
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
	parent = models.ForeignKey(
		'self',
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name='replies',
	)
	name = models.CharField(max_length=120, default='Lecteur')
	email = models.EmailField(blank=True, help_text='Optionnel — non publié')
	message = models.TextField(max_length=1000)
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
