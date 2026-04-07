import json
import re
from datetime import timedelta
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import ArticleForm, AuthorSignupForm, ReaderCommentForm
from .models import ActionLog, AnalyticsEvent, Article, ArticleAnalytics, ReaderComment


def custom_404(request, exception=None):
	return render(request, '404.html', status=404)


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
	# Respect per-article analytics opt-out
	analytics_enabled = True
	if article is not None and hasattr(article, 'enable_analytics'):
		analytics_enabled = article.enable_analytics
	if analytics_enabled:
		try:
			_external_post(settings.ACTION_LOG_ENDPOINT, log_payload)
			log.delivery_status = ActionLog.DeliveryStatus.SENT
			log.sent_at = timezone.now()
			log.last_delivery_error = ''
		except (URLError, ValueError, TypeError) as exc:
			log.delivery_status = ActionLog.DeliveryStatus.FAILED
			log.last_delivery_error = str(exc)[:500]
	else:
		log.delivery_status = ActionLog.DeliveryStatus.FAILED
		log.last_delivery_error = 'analytics disabled for this article'
	log.save(update_fields=['delivery_attempts', 'delivery_status', 'sent_at', 'last_delivery_error'])

	return log


def home(request):
	featured = (
		Article.objects.filter(status=Article.Status.PUBLISHED)
		.select_related('author')
		.prefetch_related('tags')
		.annotate(
			view_count=Count('action_logs', filter=Q(action_logs__action='article_view')),
			comment_count=Count('comments', filter=Q(comments__is_approved=True)),
			share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
		)
		.order_by('-created_at')[:6]
	)
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
	category = request.GET.get('category', '').strip()
	queryset = (
		Article.objects.filter(status=Article.Status.PUBLISHED)
		.select_related('author')
		.prefetch_related('tags')
		.annotate(
			view_count=Count('action_logs', filter=Q(action_logs__action='article_view')),
			comment_count=Count('comments', filter=Q(comments__is_approved=True)),
			share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
		)
	)

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
		queryset = queryset.order_by('-created_at')

	if tag:
		queryset = queryset.filter(tags__slug=tag)
	if category and category in Article.Category.values:
		queryset = queryset.filter(category=category)

	_log_action(request, 'article_search', payload={'query': q, 'tag': tag, 'category': category, 'result_count': queryset.count()})

	return render(
		request,
		'blog/article_list.html',
		{
			'articles': queryset,
			'query': q,
			'active_tag': tag,
			'active_category': category,
			'categories': Article.Category.choices,
		},
	)


def article_detail(request, slug):
	article = get_object_or_404(
		Article.objects.select_related('author').prefetch_related('tags'),
		slug=slug,
		status=Article.Status.PUBLISHED,
	)
	analytics, _ = ArticleAnalytics.objects.get_or_create(article=article)

	if request.method == 'POST':
		form = ReaderCommentForm(request.POST)
		parent_id = request.POST.get('parent_id', '').strip()
		if form.is_valid():
			comment = form.save(commit=False)
			comment.article = article
			if parent_id:
				try:
					parent_comment = ReaderComment.objects.get(
						id=parent_id, article=article, is_approved=True
					)
					comment.parent = parent_comment
				except (ReaderComment.DoesNotExist, ValueError):
					pass
			comment.save()
			_log_action(
				request,
				'reader_comment_created',
				article=article,
				payload={'actor_type': 'reader', 'comment_id': comment.id, 'name': comment.name},
			)
			messages.success(request, 'Votre commentaire a bien été enregistré.')
			return redirect('blog:article_detail', slug=article.slug)
	else:
		form = ReaderCommentForm()

	# Load all approved comments flat then build tree in Python.
	all_comments = list(
		ReaderComment.objects.filter(article=article, is_approved=True).order_by('created_at')
	)
	comment_map = {c.id: c for c in all_comments}
	for c in all_comments:
		c.children = []
	roots = []
	for c in all_comments:
		if c.parent_id and c.parent_id in comment_map:
			comment_map[c.parent_id].children.append(c)
		else:
			roots.append(c)
	# Newest root comments first
	roots.sort(key=lambda c: c.created_at, reverse=True)

	context = {
		'article': article,
		'objectives': _parse_lines(article.objectives),
		'reflection_questions': _parse_lines(article.reflection_questions),
		'resources': _parse_lines(article.resources),
		'comment_form': form,
		'comments': roots,
		'comment_count': len(all_comments),
		'share_count': ActionLog.objects.filter(action='article_share', article=article).count(),
		'analytics': analytics,
	}
	_log_action(request, 'article_view', article=article, payload={'actor_type': 'reader'})
	return render(request, 'blog/article_detail.html', context)


@login_required
def author_dashboard(request):
	own_articles = Article.objects.filter(author=request.user).prefetch_related('tags').order_by('-updated_at')
	analytics_rows = ArticleAnalytics.objects.filter(article__author=request.user).select_related('article')
	analytics_by_article = {row.article_id: row for row in analytics_rows}

	total_reads = ActionLog.objects.filter(action='article_view', article__author=request.user).count()
	total_shares = ActionLog.objects.filter(action='article_share', article__author=request.user).count()
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

	total_articles = own_articles.count()
	analysed_count = own_articles.filter(enable_analytics=True).count()
	not_analysed_count = total_articles - analysed_count
	analysed_pct = round(analysed_count * 100 / total_articles) if total_articles else 0
	not_analysed_pct = 100 - analysed_pct if total_articles else 0

	# Distribution par catégorie
	category_dist = []
	for value, label in Article.Category.choices:
		count = own_articles.filter(category=value).count()
		if count:
			category_dist.append({'value': value, 'label': label, 'count': count})
	category_dist.sort(key=lambda x: -x['count'])

	# ── Helper: French short date label ──
	_MOIS_FR = {
		1: 'janv', 2: 'fév', 3: 'mars', 4: 'avr', 5: 'mai', 6: 'juin',
		7: 'juil', 8: 'août', 9: 'sept', 10: 'oct', 11: 'nov', 12: 'déc',
	}

	def _fr_label(d):
		return f'{d.day} {_MOIS_FR[d.month]}'

	# ── Charts: articles published per day (last 30 days) ──
	thirty_days_ago = timezone.now() - timedelta(days=30)
	today = timezone.now().date()

	pub_per_day_qs = (
		Article.objects.filter(
			author=request.user,
			status=Article.Status.PUBLISHED,
			published_at__gte=thirty_days_ago,
		)
		.annotate(day=TruncDate('published_at'))
		.values('day')
		.annotate(count=Count('id'))
		.order_by('day')
	)
	pub_per_day = {r['day']: r['count'] for r in pub_per_day_qs}
	pub_labels, pub_data, pub_is_sunday = [], [], []
	for i in range(30):
		day = today - timedelta(days=29 - i)
		pub_labels.append(_fr_label(day))
		pub_data.append(pub_per_day.get(day, 0))
		pub_is_sunday.append(day.weekday() == 6)

	# ── Charts: comments per day (last 30 days) ──
	comment_per_day_qs = (
		ReaderComment.objects.filter(
			article__author=request.user,
			created_at__gte=thirty_days_ago,
		)
		.annotate(day=TruncDate('created_at'))
		.values('day')
		.annotate(count=Count('id'))
		.order_by('day')
	)
	comment_per_day = {r['day']: r['count'] for r in comment_per_day_qs}
	comment_chart_labels, comment_chart_data = [], []
	for i in range(30):
		day = today - timedelta(days=29 - i)
		comment_chart_labels.append(_fr_label(day))
		comment_chart_data.append(comment_per_day.get(day, 0))

	# ── Charts: article visits per day (last 30 days) ──
	visit_per_day_qs = (
		ActionLog.objects.filter(
			action='article_view',
			article__author=request.user,
			created_at__gte=thirty_days_ago,
		)
		.annotate(day=TruncDate('created_at'))
		.values('day')
		.annotate(count=Count('id'))
		.order_by('day')
	)
	visit_per_day = {r['day']: r['count'] for r in visit_per_day_qs}
	visit_chart_labels, visit_chart_data = [], []
	for i in range(30):
		day = today - timedelta(days=29 - i)
		visit_chart_labels.append(_fr_label(day))
		visit_chart_data.append(visit_per_day.get(day, 0))

	# ── Visit events per day (OS, browser, device) ──
	visit_logs = list(
		ActionLog.objects.filter(
			action='article_view',
			article__author=request.user,
			created_at__gte=thirty_days_ago,
		).values_list('created_at', 'user_agent')
	)

	def _parse_ua(ua):
		ua_lower = (ua or '').lower()
		if 'windows' in ua_lower:
			os_name = 'Windows'
		elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
			os_name = 'macOS'
		elif 'android' in ua_lower:
			os_name = 'Android'
		elif 'iphone' in ua_lower or 'ipad' in ua_lower:
			os_name = 'iOS'
		elif 'linux' in ua_lower:
			os_name = 'Linux'
		else:
			os_name = 'Autre'
		if 'edg' in ua_lower:
			br = 'Edge'
		elif 'opr' in ua_lower or 'opera' in ua_lower:
			br = 'Opera'
		elif 'chrome' in ua_lower:
			br = 'Chrome'
		elif 'firefox' in ua_lower:
			br = 'Firefox'
		elif 'safari' in ua_lower:
			br = 'Safari'
		else:
			br = 'Autre'
		if 'mobile' in ua_lower or 'iphone' in ua_lower:
			dev = 'Mobile'
		elif 'ipad' in ua_lower or 'tablet' in ua_lower:
			dev = 'Tablette'
		else:
			dev = 'Desktop'
		return os_name, br, dev

	# Aggregate per-day per-category
	os_per_day, browser_per_day, device_per_day = {}, {}, {}
	os_all, browser_all, device_all = set(), set(), set()
	for created_at, ua in visit_logs:
		day = created_at.date()
		os_name, br, dev = _parse_ua(ua)
		os_all.add(os_name)
		browser_all.add(br)
		device_all.add(dev)
		os_per_day.setdefault(day, {})
		os_per_day[day][os_name] = os_per_day[day].get(os_name, 0) + 1
		browser_per_day.setdefault(day, {})
		browser_per_day[day][br] = browser_per_day[day].get(br, 0) + 1
		device_per_day.setdefault(day, {})
		device_per_day[day][dev] = device_per_day[day].get(dev, 0) + 1

	os_all = sorted(os_all)
	browser_all = sorted(browser_all)
	device_all = sorted(device_all)

	days_range = [today - timedelta(days=29 - i) for i in range(30)]
	os_series = {name: [os_per_day.get(d, {}).get(name, 0) for d in days_range] for name in os_all}
	browser_series = {name: [browser_per_day.get(d, {}).get(name, 0) for d in days_range] for name in browser_all}
	device_series = {name: [device_per_day.get(d, {}).get(name, 0) for d in days_range] for name in device_all}

	# ── Comments summary ──
	all_user_comments = ReaderComment.objects.filter(article__author=request.user, is_approved=True)
	total_comments_count = all_user_comments.count()
	most_replied = (
		ReaderComment.objects.filter(article__author=request.user, is_approved=True)
		.select_related('article')
		.annotate(reply_count=Count('replies'))
		.order_by('-reply_count')
		.first()
	)
	recent_comments = list(
		ReaderComment.objects.filter(article__author=request.user, is_approved=True)
		.select_related('article')
		.order_by('-created_at')[:5]
	)
	comments_by_article = list(
		ReaderComment.objects.filter(article__author=request.user, is_approved=True)
		.values('article__title', 'article__slug')
		.annotate(count=Count('id'))
		.order_by('-count')[:5]
	)

	_log_action(request, 'author_dashboard_view', payload={'article_count': total_articles, 'total_reads': total_reads})

	return render(
		request,
		'blog/dashboard.html',
		{
			'article_cards': [
				{'article': article, 'analytics': analytics_by_article.get(article.id)}
				for article in own_articles
			],
			'total_reads': total_reads,
			'total_shares': total_shares,
			'avg_time': avg_time,
			'top_section': top_section,
			'analytics_rows': analytics_rows,
			'analytics_endpoint': settings.ANALYTICS_ENDPOINT,
			'total_articles': total_articles,
			'analysed_count': analysed_count,
			'not_analysed_count': not_analysed_count,
			'analysed_pct': analysed_pct,
			'not_analysed_pct': not_analysed_pct,
			'category_dist': category_dist,
			# Charts JSON data
			'pub_labels_json': json.dumps(pub_labels),
			'pub_data_json': json.dumps(pub_data),
			'pub_is_sunday_json': json.dumps(pub_is_sunday),
			'comment_chart_labels_json': json.dumps(comment_chart_labels),
			'comment_chart_data_json': json.dumps(comment_chart_data),
			'visit_chart_labels_json': json.dumps(visit_chart_labels),
			'visit_chart_data_json': json.dumps(visit_chart_data),
			'os_series_json': json.dumps(os_series),
			'browser_series_json': json.dumps(browser_series),
			'device_series_json': json.dumps(device_series),
			# Comments summary
			'total_comments_count': total_comments_count,
			'most_replied': most_replied,
			'recent_comments': recent_comments,
			'comments_by_article': comments_by_article,
		},
	)
	



@login_required
def article_create(request):
	if request.method == 'POST':
		form = ArticleForm(request.POST, request.FILES)
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
		form = ArticleForm(request.POST, request.FILES, instance=article)
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



@csrf_exempt
@require_POST
def track_share(request):
	try:
		payload = json.loads(request.body.decode('utf-8'))
	except json.JSONDecodeError:
		return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
	article_id = payload.get('article_id')
	if not article_id:
		return JsonResponse({'ok': False, 'error': 'missing article_id'}, status=400)
	article = get_object_or_404(Article, id=article_id, status=Article.Status.PUBLISHED)
	_log_action(request, 'article_share', article=article, payload={'actor_type': 'reader'})
	share_count = ActionLog.objects.filter(action='article_share', article=article).count()
	return JsonResponse({'ok': True, 'share_count': share_count})


def logout_view(request):
	from django.contrib.auth import logout
	_log_action(request, 'author_logout')
	logout(request)
	messages.info(request, 'Vous avez ete deconnecte.')
	return redirect('blog:home')