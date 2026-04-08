import json
from datetime import date, timedelta
from pyexpat.errors import messages

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import logout as auth_logout


from . import services as db_utils
from .models import Article, ArticleMetrics, DailyReads, RawEvent, Teacher


# ---------------------------------------------------------------------------
# Public – API documentation page (no login required)
# ---------------------------------------------------------------------------

def api_docs(request):
    """Public landing page: API reference for the Digital Scholar server."""
    return render(
        request, 'analytics/api_docs.html',
        context={'base_url': request.build_absolute_uri('/')}
    )


# ---------------------------------------------------------------------------
# Helpers (legacy – kept for receive_analytics / receive_action_log)
# ---------------------------------------------------------------------------

def _detect_device(user_agent: str) -> str:
    ua = user_agent.lower()
    if 'tablet' in ua or 'ipad' in ua:
        return 'Tablet'
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'Mobile'
    return 'Desktop'


def _detect_browser(user_agent: str) -> str:
    ua = user_agent.lower()
    if 'firefox' in ua:
        return 'Firefox'
    if 'safari' in ua and 'chrome' not in ua:
        return 'Safari'
    return 'Chrome'


def _get_or_create_teacher(payload: dict):
    uid = payload.get('user_id')
    if not uid:
        return None
    teacher, _ = Teacher.objects.get_or_create(
        client_user_id=uid,
        defaults={
            'username': payload.get('username', f'user_{uid}'),
            'first_name': payload.get('first_name', ''),
            'last_name': payload.get('last_name', ''),
        },
    )
    return teacher


def _get_or_create_article(payload: dict, teacher):
    aid = payload.get('article_id')
    if not aid:
        return None
    article, created = Article.objects.get_or_create(
        client_article_id=aid,
        defaults={
            'teacher': teacher,
            'title': payload.get('article_title', f'Article #{aid}'),
            'slug': payload.get('slug', ''),
            'category': payload.get('category', ''),
            'word_count': payload.get('word_count', 0),
            'published_at': payload.get('published_at'),
        },
    )
    if not created and teacher and article.teacher_id != teacher.id:
        article.teacher = teacher
        article.save(update_fields=['teacher'])
    return article


# ---------------------------------------------------------------------------
# Legacy API – receive analytics/action-log push events from client
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def receive_analytics(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    ua = request.META.get('HTTP_USER_AGENT', '')
    teacher = _get_or_create_teacher(payload)
    article = _get_or_create_article(payload, teacher)

    section = (payload.get('section') or '').lower()
    duration = max(int(payload.get('duration_seconds', 0)), 0)

    if article:
        metrics, _ = ArticleMetrics.objects.get_or_create(article=article)
        if section == 'article':
            metrics.total_reads += 1
            metrics.total_seconds_read += duration
        elif section == 'introduction':
            metrics.intro_seconds += duration
        elif section == 'objectifs':
            metrics.objectives_seconds += duration
        elif section == 'contenu':
            metrics.content_seconds += duration
        elif section == 'conclusion':
            metrics.conclusion_seconds += duration
        elif section == 'ressources':
            metrics.resources_seconds += duration
        metrics.save()

        if section == 'article':
            today = date.today()
            dr, _ = DailyReads.objects.get_or_create(article=article, date=today)
            dr.reads += 1
            dr.save(update_fields=['reads'])

    RawEvent.objects.create(
        event_type=RawEvent.EventType.ANALYTICS,
        teacher=teacher,
        article=article,
        section=section,
        duration_seconds=duration,
        session_id=payload.get('session_id', ''),
        device_type=_detect_device(ua),
        browser=_detect_browser(ua),
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=ua[:255],
        payload=payload,
    )
    return JsonResponse({'ok': True})


@csrf_exempt
@require_POST
def receive_action_log(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    ua = request.META.get('HTTP_USER_AGENT', '')
    teacher = _get_or_create_teacher(payload)
    article = _get_or_create_article(payload, teacher)

    RawEvent.objects.create(
        event_type=RawEvent.EventType.ACTION_LOG,
        teacher=teacher,
        article=article,
        action=payload.get('action', ''),
        actor_type=payload.get('actor_type', ''),
        session_id=payload.get('session_id', ''),
        device_type=_detect_device(ua),
        browser=_detect_browser(ua),
        ip_address=payload.get('ip_address') or request.META.get('REMOTE_ADDR', ''),
        user_agent=ua[:255],
        payload=payload,
    )
    return JsonResponse({'ok': True})


# =========================================================================
# Dashboard (uses synced client_* models via db_utils_v2)
# =========================================================================

@login_required
def dashboard(request):
    period_type = request.GET.get('period_type', '')
    period_value = request.GET.get('period_value', '')

    current_year = timezone.now().year
    monthly_reads = db_utils.get_monthly_reads(current_year)

    now_month = timezone.now().month
    this_month = monthly_reads[now_month - 1]
    last_month = monthly_reads[now_month - 2] if now_month >= 2 else 0
    pct_change = round((this_month - last_month) / last_month * 100, 1) if last_month else 0

    months_fr = ['Jan', 'Feb', 'Mar', 'Avr', 'Mai', 'Jun',
                 'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']

    analytics_stats = db_utils.get_analytics_tracking_stats()
    category_dist = db_utils.get_category_distribution()
    articles_daily = db_utils.get_articles_published_daily(30)
    comments_daily = db_utils.get_comments_daily(30)
    visits_daily = db_utils.get_visits_daily(30)
    os_data = db_utils.get_os_breakdown(30)
    browser_data = db_utils.get_browser_breakdown_full(30)
    device_data = db_utils.get_device_breakdown_full(30)
    comment_overview = db_utils.get_comment_overview()
    registrations_daily = db_utils.get_registrations_daily(30)
    top_articles = db_utils.get_top_articles_full(5)
    all_articles = db_utils.get_all_articles_table()

    period_data = None
    if period_type and period_value:
        period_data = db_utils.get_dashboard_for_period(period_type, period_value)

    context = {
        'total_articles': db_utils.get_total_articles(),
        'total_teachers': db_utils.get_total_teachers(),
        'total_reads': db_utils.get_total_reads(),
        'avg_read_time': db_utils.get_avg_read_time(),
        'total_comments': db_utils.get_total_comments(),
        'total_shares': db_utils.get_total_shares(),
        'total_users': db_utils.get_total_users(),
        'top_teacher': db_utils.get_top_teacher_week(),
        'monthly_reads': monthly_reads,
        'months_fr': months_fr,
        'pct_change': pct_change,
        'analytics_stats': analytics_stats,
        'analytics_stats_json': json.dumps(analytics_stats),
        'category_dist': category_dist,
        'category_dist_json': json.dumps(category_dist),
        'articles_daily_json': json.dumps(articles_daily),
        'comments_daily_json': json.dumps(comments_daily),
        'visits_daily_json': json.dumps(visits_daily),
        'os_data_json': json.dumps(os_data),
        'browser_data_json': json.dumps(browser_data),
        'device_data_json': json.dumps(device_data),
        'comment_overview': comment_overview,
        'registrations_daily_json': json.dumps(registrations_daily),
        'top_most_read': top_articles['most_read'],
        'top_most_commented': top_articles['most_commented'],
        'top_most_shared': top_articles['most_shared'],
        'all_articles': all_articles,
        'period_type': period_type,
        'period_value': period_value,
        'period_data': period_data,
        'period_data_json': json.dumps(period_data) if period_data else 'null',
    }
    return render(request, 'analytics/dashboard.html', context)


# =========================================================================
# Explorateur
# =========================================================================

@login_required
def explorateur(request):
    date_str = request.GET.get('date', '')
    teacher_id = request.GET.get('teacher', '')
    tag_name = request.GET.get('category', '')
    device = request.GET.get('device', 'Tous')

    teachers = db_utils.get_all_teachers()
    categories = db_utils.get_all_tags()

    events = db_utils.get_raw_events(
        date_str=date_str,
        teacher_id=teacher_id,
        tag_name=tag_name,
    )

    bar_data, cat_colors, days_fr = db_utils.get_bar_chart_data()

    cat_totals = {c: sum(v) for c, v in bar_data.items()}
    grand_total = sum(cat_totals.values())
    dominant_cat = max(cat_totals, key=cat_totals.get) if cat_totals else ''
    dominant_pct = (
        round(cat_totals.get(dominant_cat, 0) / grand_total * 100)
        if grand_total else 0
    )

    context = {
        'teachers': teachers,
        'categories': categories,
        'devices': ['Tous', 'Mobile', 'Desktop', 'Tablet'],
        'events': events,
        'days_fr': days_fr,
        'bar_data_json': json.dumps(bar_data),
        'cat_colors_json': json.dumps(cat_colors),
        'selected_teacher': teacher_id,
        'selected_category': tag_name,
        'selected_device': device,
        'selected_date': date_str,
        'dominant_cat': dominant_cat,
        'dominant_pct': dominant_pct,
    }
    return render(request, 'analytics/explorateur.html', context)


# =========================================================================
# Tendances
# =========================================================================

@login_required
def tendances(request):
    period = request.GET.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    since = date.today() - timedelta(days=days)

    metrics = db_utils.get_tendances_metrics()
    device_data = db_utils.get_device_breakdown(since)
    browser_data = db_utils.get_browser_breakdown(since)
    impressions = db_utils.get_total_impressions(since)
    retention = db_utils.get_retention_pct(since)

    max_secs = metrics[0]['total_seconds'] if metrics else 1

    context = {
        'period': period,
        'metrics': metrics,
        'max_secs': max_secs,
        'device_data': device_data,
        'browser_data': browser_data,
        'total_impressions': f"{impressions:,}".replace(',', '\u202f'),
        'retention_pct': retention,
    }
    return render(request, 'analytics/tendances.html', context)


# =========================================================================
# Article detail & list
# =========================================================================

@login_required
def article_detail(request, pk):
    article = db_utils.get_article_detail(pk)
    if article is None:
        from django.http import Http404
        raise Http404

    last7, days_labels = db_utils.get_article_last7_reads(pk)

    wc = article['word_count'] or 1200
    structure = {
        'Intro': round(wc * 0.17),
        'Analyse Centrale': round(wc * 0.67),
        'Conclusion': round(wc * 0.17),
    }

    context = {
        'article': article,
        'last7': last7,
        'days_labels': days_labels,
        'structure': structure,
        'breadcrumb_category': (article['tags'] or '').split(',')[0] or 'Pedagogie',
    }
    return render(request, 'analytics/article_detail.html', context)


@login_required
def article_list(request):
    articles = db_utils.get_articles_list()
    return render(request, 'analytics/article_list.html', {'articles': articles})


# =========================================================================
# Author analytics (NEW)
# =========================================================================

@login_required
def auteur_list(request):
    authors = db_utils.get_all_teachers()
    from .models import ClientArticle, ClientArticleAnalytics, ClientReaderComment
    from django.db.models import Sum
    for a in authors:
        uid = a['id']
        a['article_count'] = ClientArticle.objects.filter(author_id=uid).count()
        a['published_count'] = ClientArticle.objects.filter(author_id=uid, status='published').count()
        a['total_reads'] = ClientArticleAnalytics.objects.filter(
            article__author_id=uid
        ).aggregate(t=Sum('total_reads'))['t'] or 0
        a['total_comments'] = ClientReaderComment.objects.filter(article__author_id=uid).count()
    return render(request, 'analytics/auteur_list.html', {'authors': authors})


@login_required
def auteur_detail(request, pk):
    data = db_utils.get_author_detail(pk)
    if data is None:
        from django.http import Http404
        raise Http404

    daily_reads = db_utils.get_author_daily_reads(pk, 30)

    context = {
        **data,
        'daily_reads_json': json.dumps(daily_reads),
        'sections_json': json.dumps(data['sections']),
        'category_dist_json': json.dumps(data['category_dist']),
    }
    return render(request, 'analytics/auteur_detail.html', context)


# =========================================================================
# User activity tab (NEW)
# =========================================================================

@login_required
def utilisateurs(request):
    users = db_utils.get_all_users_activity()
    actions_daily = db_utils.get_user_actions_daily(30)

    context = {
        'users': users,
        'total_users': len(users),
        'active_users': sum(1 for u in users if u['article_count'] > 0),
        'actions_daily_json': json.dumps(actions_daily),
    }
    return render(request, 'analytics/utilisateurs.html', context)





def logout_v(request):
	from django.contrib.auth import logout
	auth_logout(request, 'author_logout')
	logout(request)
	messages.info(request, 'Vous avez ete deconnecte.')
	return redirect('api_docs')