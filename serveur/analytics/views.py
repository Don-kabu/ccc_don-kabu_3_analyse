import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import db_utils


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
# API – receive push events from the client app (kept for future use)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def receive_analytics(request):
    """Accepts analytics JSON pushed by the client blog (optional path)."""
    try:
        json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    return JsonResponse({'ok': True})


@csrf_exempt
@require_POST
def receive_action_log(request):
    """Accepts action-log JSON pushed by the client blog (optional path)."""
    try:
        json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------------------
# Dashboard – Design 1
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    current_year = timezone.now().year
    monthly_reads = db_utils.get_monthly_reads(current_year)

    now_month = timezone.now().month
    this_month = monthly_reads[now_month - 1]
    last_month = monthly_reads[now_month - 2] if now_month >= 2 else 0
    pct_change = round((this_month - last_month) / last_month * 100, 1) if last_month else 0

    months_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

    context = {
        'total_articles': db_utils.get_total_articles(),
        'total_teachers': db_utils.get_total_teachers(),
        'top_teacher':    db_utils.get_top_teacher_week(),
        'top_articles':   db_utils.get_top_articles(5),
        'monthly_reads':  monthly_reads,
        'months_fr':      months_fr,
        'pct_change':     pct_change,
    }
    return render(request, 'analytics/dashboard.html', context)


# ---------------------------------------------------------------------------
# Explorateur de Mesures – Design 2
# ---------------------------------------------------------------------------

@login_required
def explorateur(request):
    date_str  = request.GET.get('date', '')
    teacher_id = request.GET.get('teacher', '')
    tag_name  = request.GET.get('category', '')
    device    = request.GET.get('device', 'Tous')

    teachers   = db_utils.get_all_teachers()
    categories = db_utils.get_all_tags()

    events = db_utils.get_raw_events(
        date_str=date_str,
        teacher_id=teacher_id,
        tag_name=tag_name,
    )

    bar_data, cat_colors, days_fr = db_utils.get_bar_chart_data()

    cat_totals   = {c: sum(v) for c, v in bar_data.items()}
    grand_total  = sum(cat_totals.values())
    dominant_cat = max(cat_totals, key=cat_totals.get) if cat_totals else ''
    dominant_pct = (
        round(cat_totals.get(dominant_cat, 0) / grand_total * 100)
        if grand_total else 0
    )

    context = {
        'teachers':         teachers,
        'categories':       categories,
        'devices':          ['Tous', 'Mobile', 'Desktop', 'Tablet'],
        'events':           events,
        'days_fr':          days_fr,
        'bar_data_json':    json.dumps(bar_data),
        'cat_colors_json':  json.dumps(cat_colors),
        'selected_teacher': teacher_id,
        'selected_category': tag_name,
        'selected_device':  device,
        'selected_date':    date_str,
        'dominant_cat':     dominant_cat,
        'dominant_pct':     dominant_pct,
    }
    return render(request, 'analytics/explorateur.html', context)


# ---------------------------------------------------------------------------
# Analyse & Visualisation des Tendances – Design 3
# ---------------------------------------------------------------------------

@login_required
def tendances(request):
    period = request.GET.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    since = date.today() - timedelta(days=days)

    metrics      = db_utils.get_tendances_metrics()
    device_data  = db_utils.get_device_breakdown(since)
    browser_data = db_utils.get_browser_breakdown(since)
    impressions  = db_utils.get_total_impressions(since)
    retention    = db_utils.get_retention_pct(since)

    max_secs = metrics[0]['total_seconds'] if metrics else 1

    context = {
        'period':            period,
        'metrics':           metrics,
        'max_secs':          max_secs,
        'device_data':       device_data,
        'browser_data':      browser_data,
        'total_impressions': f"{impressions:,}".replace(',', '\u202f'),
        'retention_pct':     retention,
    }
    return render(request, 'analytics/tendances.html', context)


# ---------------------------------------------------------------------------
# Article Detail Analytics – Design 4
# ---------------------------------------------------------------------------

@login_required
def article_detail(request, pk):
    article = db_utils.get_article_detail(pk)
    if article is None:
        from django.http import Http404
        raise Http404

    last7, days_labels = db_utils.get_article_last7_reads(pk)

    wc = article['word_count'] or 1200
    structure = {
        'Intro':           round(wc * 0.17),
        'Analyse Centrale': round(wc * 0.67),
        'Conclusion':      round(wc * 0.17),
    }

    context = {
        'article':             article,
        'last7':               last7,
        'days_labels':         days_labels,
        'structure':           structure,
        'breadcrumb_category': (article['tags'] or '').split(',')[0] or 'Pédagogie',
    }
    return render(request, 'analytics/article_detail.html', context)


# ---------------------------------------------------------------------------
# Article list
# ---------------------------------------------------------------------------

@login_required
def article_list(request):
    articles = db_utils.get_articles_list()
    return render(request, 'analytics/article_list.html', {'articles': articles})


from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Article, ArticleMetrics, DailyReads, RawEvent, Teacher


# ---------------------------------------------------------------------------
# Helpers
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
# API – receive analytics events from the client app
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def receive_analytics(request):
    """Endpoint that receives analytics tracking events from the client blog."""
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
    """Endpoint that receives action log events from the client blog."""
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


# ---------------------------------------------------------------------------
# Dashboard – Design 1
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    total_articles = Article.objects.count()
    total_teachers = Teacher.objects.count()

    current_year = timezone.now().year
    monthly_reads = [0] * 12
    for dr in DailyReads.objects.filter(date__year=current_year):
        monthly_reads[dr.date.month - 1] += dr.reads

    week_start = date.today() - timedelta(days=date.today().weekday())
    top_teacher = None
    top_teacher_reads = 0
    for teacher in Teacher.objects.all():
        reads = DailyReads.objects.filter(
            article__teacher=teacher,
            date__gte=week_start,
        ).aggregate(total=Sum('reads'))['total'] or 0
        if reads > top_teacher_reads:
            top_teacher_reads = reads
            top_teacher = teacher

    top_articles = (
        ArticleMetrics.objects
        .select_related('article__teacher')
        .order_by('-total_reads')[:5]
    )

    months_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

    now_month = timezone.now().month
    this_month = monthly_reads[now_month - 1]
    last_month = monthly_reads[now_month - 2] if now_month >= 2 else 0
    if last_month:
        pct_change = round((this_month - last_month) / last_month * 100, 1)
    else:
        pct_change = 0

    context = {
        'total_articles': total_articles,
        'total_teachers': total_teachers,
        'top_teacher': top_teacher,
        'top_articles': top_articles,
        'monthly_reads': monthly_reads,
        'months_fr': months_fr,
        'pct_change': pct_change,
    }
    return render(request, 'analytics/dashboard.html', context)


# ---------------------------------------------------------------------------
# Explorateur de Mesures – Design 2
# ---------------------------------------------------------------------------

@login_required
def explorateur(request):
    date_str = request.GET.get('date', '')
    teacher_id = request.GET.get('teacher', '')
    category = request.GET.get('category', '')
    device = request.GET.get('device', 'Tous')

    teachers = Teacher.objects.order_by('last_name', 'first_name')
    categories = list(Article.objects.values_list('category', flat=True).distinct().exclude(category=''))

    events_qs = RawEvent.objects.filter(
        event_type=RawEvent.EventType.ANALYTICS,
    ).select_related('teacher', 'article').order_by('-received_at')

    if date_str:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            events_qs = events_qs.filter(received_at__date=filter_date)
        except ValueError:
            pass

    if teacher_id:
        events_qs = events_qs.filter(teacher_id=teacher_id)

    if category:
        events_qs = events_qs.filter(article__category=category)

    if device and device != 'Tous':
        events_qs = events_qs.filter(device_type=device)

    events = list(events_qs[:50])

    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven']
    cat_colors = {'Pédagogie': '#254e70', 'Histoire': '#527a55', 'Sciences': '#6aaa64'}

    all_cats = categories[:3]
    bar_data = {cat: [0] * 5 for cat in all_cats}
    for dr in DailyReads.objects.select_related('article'):
        cat = dr.article.category
        if cat in bar_data:
            dow = dr.date.weekday()
            if dow < 5:
                bar_data[cat][dow] += dr.reads

    cat_totals = {c: sum(v) for c, v in bar_data.items()}
    dominant_cat = max(cat_totals, key=cat_totals.get) if cat_totals else ''
    grand_total = sum(cat_totals.values())
    dominant_pct = round(cat_totals.get(dominant_cat, 0) / grand_total * 100) if grand_total else 0

    context = {
        'teachers': teachers,
        'categories': all_cats,
        'devices': ['Tous', 'Mobile', 'Desktop', 'Tablet'],
        'events': events,
        'days_fr': days_fr,
        'bar_data_json': json.dumps(bar_data),
        'cat_colors_json': json.dumps(cat_colors),
        'selected_teacher': teacher_id,
        'selected_category': category,
        'selected_device': device,
        'selected_date': date_str,
        'dominant_cat': dominant_cat,
        'dominant_pct': dominant_pct,
    }
    return render(request, 'analytics/explorateur.html', context)


# ---------------------------------------------------------------------------
# Analyse & Visualisation des Tendances – Design 3
# ---------------------------------------------------------------------------

@login_required
def tendances(request):
    period = request.GET.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    since = date.today() - timedelta(days=days)

    metrics = (
        ArticleMetrics.objects
        .select_related('article')
        .order_by('-total_seconds_read')[:6]
    )

    device_counts = (
        RawEvent.objects
        .filter(received_at__date__gte=since, section='article')
        .values('device_type')
        .annotate(cnt=Count('id'))
    )
    total_device = sum(d['cnt'] for d in device_counts) or 1
    device_data = [
        {'label': d['device_type'] or 'Desktop', 'pct': round(d['cnt'] / total_device * 100)}
        for d in device_counts
    ]

    browser_counts = (
        RawEvent.objects
        .filter(received_at__date__gte=since)
        .values('browser')
        .annotate(cnt=Count('id'))
    )
    total_browser = sum(b['cnt'] for b in browser_counts) or 1
    browser_data = [
        {'label': b['browser'] or 'Chrome', 'pct': round(b['cnt'] / total_browser * 100)}
        for b in browser_counts
    ]

    total_impressions = (
        ArticleMetrics.objects
        .filter(updated_at__date__gte=since)
        .aggregate(total=Sum('total_reads'))['total'] or 0
    )

    retention = (
        RawEvent.objects
        .filter(received_at__date__gte=since, section='article', duration_seconds__gt=0)
        .aggregate(avg=Avg('duration_seconds'))['avg'] or 0
    )
    retention_pct = min(round(retention / 900 * 100), 100)

    context = {
        'period': period,
        'metrics': metrics,
        'device_data': device_data,
        'browser_data': browser_data,
        'total_impressions': f"{total_impressions:,}".replace(',', '\u202f'),
        'retention_pct': retention_pct,
    }
    return render(request, 'analytics/tendances.html', context)


# ---------------------------------------------------------------------------
# Article Detail Analytics – Design 4
# ---------------------------------------------------------------------------

@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    metrics, _ = ArticleMetrics.objects.get_or_create(article=article)

    last7 = []
    days_labels = []
    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        dr = DailyReads.objects.filter(article=article, date=d).first()
        last7.append(dr.reads if dr else 0)
        days_labels.append(days_fr[d.weekday()])

    wc = article.word_count or 1200
    structure = {
        'Intro': round(wc * 0.17),
        'Analyse Centrale': round(wc * 0.67),
        'Conclusion': round(wc * 0.17),
    }

    context = {
        'article': article,
        'metrics': metrics,
        'last7': last7,
        'days_labels': days_labels,
        'structure': structure,
        'breadcrumb_category': article.category or 'Pédagogie',
    }
    return render(request, 'analytics/article_detail.html', context)


# ---------------------------------------------------------------------------
# Article list
# ---------------------------------------------------------------------------

@login_required
def article_list(request):
    articles = (
        Article.objects
        .select_related('teacher')
        .prefetch_related('metrics')
        .order_by('-metrics__total_reads')
    )
    return render(request, 'analytics/article_list.html', {'articles': articles})
