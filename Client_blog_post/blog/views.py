import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, Sum, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import ArticleForm, AuthorSignupForm, ReaderCommentForm
from .models import ActionLog, AnalyticsEvent, Article, ArticleAnalytics


def _parse_lines(text):
	return [line.strip() for line in text.splitlines() if line.strip()]


def _query_terms(raw_query):
	# Keep alphanumeric tokens and ignore one-letter terms.
	return [term for term in re.findall(r"\w+", raw_query.lower()) if len(term) > 1]


def _client_ip(request):
	xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
	if xff:
		return xff.split(',')[0].strip()
	return request.META.get('REMOTE_ADDR', '')


def _external_post(endpoint, payload):
	encoded = json.dumps(payload).encode('utf-8')
	req = Request(
		endpoint,
		data=encoded,
		headers={'Content-Type': 'application/json'},
		method='POST',
	)
	urlopen(req, timeout=2)


def _log_action(request, action, article=None, payload=None, user=None):
	if user is None and request and getattr(request, 'user', None) and request.user.is_authenticated:
		user = request.user

	actor_type = 'author' if user else 'anonymous'
	if not user and payload and payload.get('actor_type') == 'reader':
		actor_type = 'reader'

	log = ActionLog.objects.create(
		action=action,
		actor_type=actor_type,
		user=user,
		article=article,
		request_path=request.path if request else '',
		request_method=request.method if request else '',
		ip_address=_client_ip(request) if request else '',
		user_agent=(request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''),
		session_id=(request.session.session_key or '' if request and getattr(request, 'session', None) else ''),
		payload=payload or {},
	)

	log_payload = {
		'type': 'action_log',
		'log_id': log.id,
		'action': log.action,
		'actor_type': log.actor_type,
		'user_id': log.user_id,
		'article_id': log.article_id,
		'request_path': log.request_path,
		'request_method': log.request_method,
		'ip_address': log.ip_address,
		'user_agent': log.user_agent,
		'session_id': log.session_id,
		'payload': log.payload,
		'created_at': log.created_at.isoformat(),
	}

	log.delivery_attempts += 1
	try:
		_external_post(settings.ACTION_LOG_ENDPOINT, log_payload)
		log.delivery_status = ActionLog.DeliveryStatus.SENT
		log.sent_at = timezone.now()
		log.last_delivery_error = ''
	except (URLError, ValueError, TypeError) as exc:
		log.delivery_status = ActionLog.DeliveryStatus.FAILED
		log.last_delivery_error = str(exc)[:500]
	log.save(update_fields=['delivery_attempts', 'delivery_status', 'sent_at', 'last_delivery_error'])

	return log


def home(request):
	featured = Article.objects.filter(status=Article.Status.PUBLISHED).select_related('author').prefetch_related('tags')[:4]
	_log_action(request, 'home_view', payload={'featured_count': featured.count()})
	return render(request, 'blog/home.html', {'featured_articles': featured})


def signup(request):
	if request.user.is_authenticated:
		return redirect('blog:author_dashboard')

	if request.method == 'POST':
		form = AuthorSignupForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			_log_action(request, 'author_signup', user=user, payload={'username': user.username})
			messages.success(request, 'Votre compte auteur a ete cree avec succes.')
			return redirect('blog:author_dashboard')
	else:
		form = AuthorSignupForm()

	return render(request, 'registration/signup.html', {'form': form})


def article_list(request):
	q = request.GET.get('q', '').strip()
	tag = request.GET.get('tag', '').strip()
	queryset = Article.objects.filter(status=Article.Status.PUBLISHED).select_related('author').prefetch_related('tags')

	if q:
		terms = _query_terms(q)
		if not terms:
			terms = [q.lower()]

		score = Value(0, output_field=IntegerField())
		for term in terms:
			score = score + Case(When(title__icontains=term, then=Value(12)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(tags__name__icontains=term, then=Value(10)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(intro__icontains=term, then=Value(8)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(content__icontains=term, then=Value(6)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(objectives__icontains=term, then=Value(5)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(conclusion__icontains=term, then=Value(4)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(reflection_questions__icontains=term, then=Value(3)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(resources__icontains=term, then=Value(3)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(author__username__icontains=term, then=Value(2)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(author__first_name__icontains=term, then=Value(2)), default=Value(0), output_field=IntegerField())
			score = score + Case(When(author__last_name__icontains=term, then=Value(2)), default=Value(0), output_field=IntegerField())

		# Bonus when the full phrase appears together in strategic fields.
		score = score + Case(When(title__icontains=q, then=Value(8)), default=Value(0), output_field=IntegerField())
		score = score + Case(When(content__icontains=q, then=Value(5)), default=Value(0), output_field=IntegerField())

		queryset = (
			queryset.annotate(search_score=score)
			.filter(search_score__gt=0)
			.distinct()
			.order_by('-search_score', '-published_at', '-updated_at')
		)
	else:
		queryset = queryset.order_by('-published_at', '-updated_at')
	if tag:
		queryset = queryset.filter(tags__slug=tag)

	_log_action(request, 'article_search', payload={'query': q, 'tag': tag, 'result_count': queryset.count()})

	return render(
		request,
		'blog/article_list.html',
		{
			'articles': queryset,
			'query': q,
			'active_tag': tag,
		},
	)


def article_detail(request, slug):
	article = get_object_or_404(
		Article.objects.select_related('author').prefetch_related('tags', 'comments'),
		slug=slug,
		status=Article.Status.PUBLISHED,
	)
	analytics, _ = ArticleAnalytics.objects.get_or_create(article=article)

	if request.method == 'POST':
		form = ReaderCommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.article = article
			comment.save()
			_log_action(
				request,
				'reader_comment_created',
				article=article,
				payload={'actor_type': 'reader', 'comment_id': comment.id, 'name': comment.name},
			)
			messages.success(request, 'Votre question/commentaire a bien ete enregistre.')
			return redirect('blog:article_detail', slug=article.slug)
	else:
		form = ReaderCommentForm()

	context = {
		'article': article,
		'objectives': _parse_lines(article.objectives),
		'reflection_questions': _parse_lines(article.reflection_questions),
		'resources': _parse_lines(article.resources),
		'comment_form': form,
		'comments': article.comments.filter(is_approved=True).order_by('-created_at')[:10],
		'analytics': analytics,
	}
	_log_action(request, 'article_view', article=article, payload={'actor_type': 'reader'})
	return render(request, 'blog/article_detail.html', context)


@login_required
def author_dashboard(request):
	own_articles = Article.objects.filter(author=request.user).prefetch_related('tags').order_by('-updated_at')
	analytics_rows = ArticleAnalytics.objects.filter(article__author=request.user).select_related('article')
	analytics_by_article = {row.article_id: row for row in analytics_rows}

	total_reads = analytics_rows.aggregate(total=Sum('total_reads'))['total'] or 0
	total_seconds = analytics_rows.aggregate(total=Sum('total_seconds_read'))['total'] or 0
	avg_time = round((total_seconds / total_reads), 1) if total_reads else 0

	top_section = 'Aucune donnee'
	if analytics_rows.exists():
		section_totals = {'intro': 0, 'objectives': 0, 'content': 0, 'conclusion': 0, 'resources': 0}
		for row in analytics_rows:
			section_totals['intro'] += row.intro_seconds
			section_totals['objectives'] += row.objectives_seconds
			section_totals['content'] += row.content_seconds
			section_totals['conclusion'] += row.conclusion_seconds
			section_totals['resources'] += row.resources_seconds

		names = {
			'intro': 'Introduction',
			'objectives': 'Objectifs',
			'content': 'Contenu',
			'conclusion': 'Conclusion',
			'resources': 'Ressources',
		}
		top_section = names[max(section_totals, key=section_totals.get)]

	_log_action(request, 'author_dashboard_view', payload={'article_count': own_articles.count(), 'total_reads': total_reads})

	return render(
		request,
		'blog/dashboard.html',
		{
			'article_cards': [
				{'article': article, 'analytics': analytics_by_article.get(article.id)}
				for article in own_articles
			],
			'total_reads': total_reads,
			'avg_time': avg_time,
			'top_section': top_section,
			'analytics_rows': analytics_rows,
			'analytics_endpoint': settings.ANALYTICS_ENDPOINT,
		},
	)


@login_required
def article_create(request):
	if request.method == 'POST':
		form = ArticleForm(request.POST)
		if form.is_valid():
			article = form.save(commit=False)
			article.author = request.user
			if article.status == Article.Status.PUBLISHED and not article.published_at:
				article.published_at = timezone.now()
			article.save()
			form.instance = article
			form.save()
			_log_action(request, 'article_created', article=article, payload={'status': article.status, 'title': article.title})
			messages.success(request, 'Article enregistre avec succes.')
			return redirect('blog:author_dashboard')
	else:
		form = ArticleForm()

	return render(request, 'blog/article_form.html', {'form': form, 'mode': 'create'})


@login_required
def article_edit(request, slug):
	article = get_object_or_404(Article, slug=slug, author=request.user)
	if request.method == 'POST':
		form = ArticleForm(request.POST, instance=article)
		if form.is_valid():
			article = form.save(commit=False)
			if article.status == Article.Status.PUBLISHED and not article.published_at:
				article.published_at = timezone.now()
			article.save()
			form.instance = article
			form.save()
			_log_action(request, 'article_updated', article=article, payload={'status': article.status, 'title': article.title})
			messages.success(request, 'Article modifie avec succes.')
			return redirect('blog:author_dashboard')
	else:
		form = ArticleForm(instance=article)

	return render(request, 'blog/article_form.html', {'form': form, 'mode': 'edit', 'article': article})


@login_required
def article_delete(request, slug):
	article = get_object_or_404(Article, slug=slug, author=request.user)
	if request.method == 'POST':
		deleted_payload = {'title': article.title, 'slug': article.slug}
		article.delete()
		_log_action(request, 'article_deleted', payload=deleted_payload)
		messages.success(request, 'Article supprime.')
		return redirect('blog:author_dashboard')
	return render(request, 'blog/article_delete.html', {'article': article})


@csrf_exempt
@require_POST
def track_analytics(request):
	try:
		payload = json.loads(request.body.decode('utf-8'))
	except json.JSONDecodeError:
		return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

	article_id = payload.get('article_id')
	section = (payload.get('section') or '').lower()
	duration_seconds = max(int(payload.get('duration_seconds', 0)), 0)
	session_id = payload.get('session_id', '')

	if not article_id or not section:
		return JsonResponse({'ok': False, 'error': 'missing fields'}, status=400)

	article = get_object_or_404(Article, id=article_id, status=Article.Status.PUBLISHED)
	analytics, _ = ArticleAnalytics.objects.get_or_create(article=article)
	AnalyticsEvent.objects.create(
		article=article,
		section=section,
		duration_seconds=duration_seconds,
		session_id=session_id,
	)

	if section == 'article':
		analytics.total_reads += 1
		analytics.total_seconds_read += duration_seconds
	elif section == 'introduction':
		analytics.intro_seconds += duration_seconds
	elif section == 'objectifs':
		analytics.objectives_seconds += duration_seconds
	elif section == 'contenu':
		analytics.content_seconds += duration_seconds
	elif section == 'conclusion':
		analytics.conclusion_seconds += duration_seconds
	elif section == 'ressources':
		analytics.resources_seconds += duration_seconds

	analytics.save()
	_log_action(
		request,
		'analytics_tracked',
		article=article,
		payload={
			'actor_type': 'reader',
			'section': section,
			'duration_seconds': duration_seconds,
			'session_id': session_id,
		},
	)

	try:
		_external_post(settings.ANALYTICS_ENDPOINT, payload)
	except (URLError, ValueError, TypeError):
		pass

	return JsonResponse({'ok': True})



def logout_view(request):
	from django.contrib.auth import logout
	_log_action(request, 'author_logout')
	logout(request)
	messages.info(request, 'Vous avez ete deconnecte.')
	return redirect('blog:home')