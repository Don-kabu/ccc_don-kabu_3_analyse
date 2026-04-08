"""
db_utils.py – ORM-based helpers querying the local client_* models.

All data is synced from the client application via the sync API.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from .models import (
    ClientActionLog,
    ClientArticle,
    ClientArticleAnalytics,
    ClientReaderComment,
    ClientTag,
    ClientUser,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _display(user: ClientUser) -> str:
    return user.display_name if user else '—'


def _visibility(total_seconds: int, total_reads: int, word_count: int) -> int:
    if not total_reads:
        return 0
    expected = max(word_count, 1) * 0.25
    ratio = min((total_seconds / total_reads) / expected, 1.0)
    return round(ratio * 100)


def _fill_days(rows_dict: dict, days: int) -> list[dict]:
    """Fill gaps in a date→count dict, return list of {date, count}."""
    result = {}
    for i in range(days + 1):
        d = (date.today() - timedelta(days=days - i)).isoformat()
        result[d] = 0
    for k, v in rows_dict.items():
        key = k if isinstance(k, str) else k.isoformat()
        if key in result:
            result[key] = v
    return [{'date': k, 'count': v} for k, v in result.items()]


def _parse_ua(ua: str) -> tuple[str, str, str]:
    """Parse user-agent into (os, browser, device)."""
    ua_lower = (ua or '').lower()
    # OS
    if 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
        os_name = 'macOS'
    elif 'android' in ua_lower:
        os_name = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower or 'ios' in ua_lower:
        os_name = 'iOS'
    elif 'linux' in ua_lower:
        os_name = 'Linux'
    else:
        os_name = 'Autre'
    # Browser
    if 'edg' in ua_lower:
        browser = 'Edge'
    elif 'opr' in ua_lower or 'opera' in ua_lower:
        browser = 'Opera'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = 'Safari'
    elif 'chrome' in ua_lower:
        browser = 'Chrome'
    else:
        browser = 'Autre'
    # Device
    if 'mobile' in ua_lower or 'iphone' in ua_lower:
        device = 'Mobile'
    elif 'ipad' in ua_lower or 'tablet' in ua_lower:
        device = 'Tablet'
    else:
        device = 'Desktop'
    return os_name, browser, device


# ---------------------------------------------------------------------------
# Dashboard KPI queries
# ---------------------------------------------------------------------------

def get_total_articles() -> int:
    return ClientArticle.objects.filter(status='published').count()


def get_total_teachers() -> int:
    return ClientUser.objects.filter(articles__isnull=False).distinct().count()


def get_total_reads() -> int:
    return ClientArticleAnalytics.objects.aggregate(
        total=Sum('total_reads')
    )['total'] or 0


def get_avg_read_time() -> float:
    agg = ClientArticleAnalytics.objects.filter(total_reads__gt=0).aggregate(
        total_sec=Sum('total_seconds_read'),
        total_r=Sum('total_reads'),
    )
    if agg['total_r']:
        return round(agg['total_sec'] / agg['total_r'], 1)
    return 0.0


def get_total_comments() -> int:
    return ClientReaderComment.objects.count()


def get_total_shares() -> int:
    return ClientActionLog.objects.filter(action='article_share').count()


def get_total_users() -> int:
    return ClientUser.objects.count()


def get_monthly_reads(year: int) -> list[int]:
    rows = (
        ClientActionLog.objects
        .filter(action='article_view', created_at__year=year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(reads=Count('id'))
    )
    monthly = [0] * 12
    for r in rows:
        if r['month']:
            monthly[r['month'].month - 1] = r['reads']
    return monthly


def get_top_teacher_week() -> dict | None:
    week_start = date.today() - timedelta(days=date.today().weekday())
    rows = (
        ClientActionLog.objects
        .filter(action='article_view', created_at__date__gte=week_start, article__isnull=False)
        .values('article__author')
        .annotate(reads=Count('id'))
        .order_by('-reads')[:1]
    )
    if rows:
        user = ClientUser.objects.filter(id=rows[0]['article__author']).first()
        if user:
            return {
                'id': user.client_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'display_name': user.display_name,
                'reads': rows[0]['reads'],
            }
    # Fallback: teacher with most reads overall
    top = (
        ClientArticle.objects
        .filter(analytics__isnull=False)
        .values('author')
        .annotate(reads=Sum('analytics__total_reads'))
        .order_by('-reads')[:1]
    )
    if top:
        user = ClientUser.objects.filter(id=top[0]['author']).first()
        if user:
            return {
                'id': user.client_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'display_name': user.display_name,
                'reads': top[0]['reads'],
            }
    return None


# ---------------------------------------------------------------------------
# All teachers / tags
# ---------------------------------------------------------------------------

def get_all_teachers() -> list[dict]:
    users = (
        ClientUser.objects
        .filter(articles__isnull=False)
        .distinct()
        .order_by('last_name', 'first_name')
    )
    return [
        {
            'id': u.id,
            'client_id': u.client_id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'display_name': u.display_name,
        }
        for u in users
    ]


def get_all_tags() -> list[str]:
    return list(
        ClientTag.objects
        .filter(articles__isnull=False)
        .distinct()
        .values_list('name', flat=True)
        .order_by('name')
    )


# ---------------------------------------------------------------------------
# Analytics tracking stats
# ---------------------------------------------------------------------------

def get_analytics_tracking_stats() -> dict:
    total = ClientArticle.objects.filter(status='published').count()
    analyzed = (
        ClientArticle.objects
        .filter(status='published', analytics__total_reads__gt=0)
        .count()
    )
    return {
        'total': total,
        'analyzed': analyzed,
        'not_analyzed': total - analyzed,
        'analyzed_pct': round(analyzed / total * 100) if total else 0,
        'not_analyzed_pct': round((total - analyzed) / total * 100) if total else 0,
    }


def get_category_distribution() -> list[dict]:
    rows = (
        ClientArticle.objects
        .filter(status='published')
        .exclude(category='')
        .values('category')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
    )
    total = sum(r['cnt'] for r in rows) or 1
    colors = [
        '#e07a5f', '#3d405b', '#81b29a', '#f2cc8f', '#264653',
        '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#606c38',
    ]
    result = []
    for i, r in enumerate(rows):
        result.append({
            'category': r['category'],
            'count': r['cnt'],
            'pct': round(r['cnt'] / total * 100),
            'color': colors[i % len(colors)],
        })
    return result


# ---------------------------------------------------------------------------
# Daily time-series
# ---------------------------------------------------------------------------

def get_articles_published_daily(days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientArticle.objects
        .filter(status='published', published_at__isnull=False, published_at__date__gte=since)
        .annotate(day=TruncDate('published_at'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


def get_comments_daily(days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientReaderComment.objects
        .filter(created_at__date__gte=since)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


def get_visits_daily(days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientActionLog.objects
        .filter(action='article_view', created_at__date__gte=since)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


def get_registrations_daily(days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientUser.objects
        .filter(date_joined__date__gte=since)
        .annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


# ---------------------------------------------------------------------------
# OS / Browser / Device breakdowns
# ---------------------------------------------------------------------------

def _ua_breakdown(field_extractor, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    logs = ClientActionLog.objects.filter(
        action='article_view', created_at__date__gte=since
    ).values_list('user_agent', flat=True)
    counts = {}
    for ua in logs:
        label = field_extractor(ua)
        counts[label] = counts.get(label, 0) + 1
    total = sum(counts.values()) or 1
    return sorted(
        [{'label': k, 'count': v, 'pct': round(v / total * 100)} for k, v in counts.items()],
        key=lambda x: -x['count'],
    )


def get_os_breakdown(days: int = 30) -> list[dict]:
    return _ua_breakdown(lambda ua: _parse_ua(ua)[0], days)


def get_browser_breakdown_full(days: int = 30) -> list[dict]:
    return _ua_breakdown(lambda ua: _parse_ua(ua)[1], days)


def get_device_breakdown_full(days: int = 30) -> list[dict]:
    return _ua_breakdown(lambda ua: _parse_ua(ua)[2], days)


# ---------------------------------------------------------------------------
# Comment overview
# ---------------------------------------------------------------------------

def get_comment_overview() -> dict:
    total = ClientReaderComment.objects.count()

    most_replied_qs = (
        ClientReaderComment.objects
        .annotate(reply_count=Count('replies'))
        .select_related('article')
        .order_by('-reply_count')[:1]
    )
    most_replied = None
    if most_replied_qs:
        c = most_replied_qs[0]
        most_replied = {
            'id': c.id,
            'name': c.name,
            'message': c.message,
            'article_id': c.article_id,
            'article_title': c.article.title,
            'reply_count': c.reply_count,
        }

    top_commented = list(
        ClientReaderComment.objects
        .values('article__title', article_id_val=F('article__id'))
        .annotate(comment_count=Count('id'))
        .order_by('-comment_count')[:5]
    )
    top_commented = [
        {'id': r['article_id_val'], 'title': r['article__title'], 'comment_count': r['comment_count']}
        for r in top_commented
    ]

    recent_comments = list(
        ClientReaderComment.objects
        .select_related('article')
        .order_by('-created_at')[:5]
    )
    recent = [
        {
            'id': c.id,
            'name': c.name,
            'message': c.message,
            'created_at': c.created_at.isoformat() if c.created_at else '',
            'article_id': c.article_id,
            'article_title': c.article.title,
        }
        for c in recent_comments
    ]

    return {
        'total': total,
        'most_replied': most_replied,
        'top_commented': top_commented,
        'recent_comments': recent,
    }


# ---------------------------------------------------------------------------
# Top articles
# ---------------------------------------------------------------------------

def get_top_articles_full(limit: int = 5) -> dict:
    base = ClientArticle.objects.filter(status='published')

    most_read = list(
        base.annotate(
            total_reads=Sum('analytics__total_reads'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True)),
            share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
        ).order_by('-total_reads')[:limit]
        .values('id', 'title', 'slug', 'category', 'total_reads', 'comment_count', 'share_count')
    )
    for r in most_read:
        r['total_reads'] = r['total_reads'] or 0

    most_commented = list(
        base.annotate(
            total_reads=Sum('analytics__total_reads'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True)),
            share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
        ).order_by('-comment_count')[:limit]
        .values('id', 'title', 'slug', 'category', 'total_reads', 'comment_count', 'share_count')
    )
    for r in most_commented:
        r['total_reads'] = r['total_reads'] or 0

    most_shared = list(
        base.annotate(
            total_reads=Sum('analytics__total_reads'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True)),
            share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
        ).order_by('-share_count')[:limit]
        .values('id', 'title', 'slug', 'category', 'total_reads', 'comment_count', 'share_count')
    )
    for r in most_shared:
        r['total_reads'] = r['total_reads'] or 0

    return {
        'most_read': most_read,
        'most_commented': most_commented,
        'most_shared': most_shared,
    }


def get_all_articles_table() -> list[dict]:
    articles = (
        ClientArticle.objects
        .select_related('author')
        .annotate(
            total_reads=Sum('analytics__total_reads'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True)),
            share_count=Count('action_logs', filter=Q(action_logs__action='article_share')),
        )
        .order_by('-created_at')
    )
    result = []
    for a in articles:
        result.append({
            'id': a.id,
            'client_id': a.client_id,
            'title': a.title,
            'slug': a.slug,
            'category': a.category,
            'category_label': a.category_label,
            'status': a.status,
            'author': a.author.username if a.author else '—',
            'created_at': a.created_at.isoformat() if a.created_at else '',
            'updated_at': a.updated_at.isoformat() if a.updated_at else '',
            'published_at': a.published_at.isoformat() if a.published_at else '',
            'total_reads': a.total_reads or 0,
            'comment_count': a.comment_count or 0,
            'share_count': a.share_count or 0,
        })
    return result


# ---------------------------------------------------------------------------
# Article detail
# ---------------------------------------------------------------------------

def get_article_detail(pk: int) -> dict | None:
    try:
        a = (
            ClientArticle.objects
            .select_related('author')
            .prefetch_related('tags')
            .annotate(
                total_reads_val=Sum('analytics__total_reads'),
                total_seconds_val=Sum('analytics__total_seconds_read'),
            )
            .get(pk=pk)
        )
    except ClientArticle.DoesNotExist:
        return None

    analytics = ClientArticleAnalytics.objects.filter(article=a).first()

    return {
        'id': a.id,
        'client_id': a.client_id,
        'title': a.title,
        'slug': a.slug,
        'category': a.category,
        'category_label': a.category_label,
        'intro': a.intro,
        'content': a.content,
        'conclusion': a.conclusion,
        'published_at': a.published_at.isoformat() if a.published_at else '',
        'teacher_id': a.author.id if a.author else None,
        'teacher_client_id': a.author.client_id if a.author else None,
        'username': a.author.username if a.author else '',
        'first_name': a.author.first_name if a.author else '',
        'last_name': a.author.last_name if a.author else '',
        'teacher_display': a.author.display_name if a.author else '—',
        'tags': ', '.join(t.name for t in a.tags.all()),
        'word_count': a.word_count,
        'total_reads': (a.total_reads_val or 0),
        'total_seconds': (a.total_seconds_val or 0),
        'intro_seconds': analytics.intro_seconds if analytics else 0,
        'objectives_seconds': analytics.objectives_seconds if analytics else 0,
        'content_seconds': analytics.content_seconds if analytics else 0,
        'conclusion_seconds': analytics.conclusion_seconds if analytics else 0,
        'resources_seconds': analytics.resources_seconds if analytics else 0,
        'avg_minutes': (
            round((a.total_seconds_val or 0) / (a.total_reads_val or 1) / 60, 1)
            if (a.total_reads_val or 0) > 0 else 0
        ),
        'visibility_pct': _visibility(
            a.total_seconds_val or 0, a.total_reads_val or 0, a.word_count or 1200
        ),
    }


def get_article_last7_reads(pk: int) -> tuple[list[int], list[str]]:
    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    last7 = []
    labels = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        count = ClientActionLog.objects.filter(
            article_id=pk, action='article_view', created_at__date=d
        ).count()
        last7.append(count)
        labels.append(days_fr[d.weekday()])
    return last7, labels


# ---------------------------------------------------------------------------
# Articles list
# ---------------------------------------------------------------------------

def get_articles_list() -> list[dict]:
    articles = (
        ClientArticle.objects
        .filter(status='published')
        .select_related('author')
        .prefetch_related('tags')
        .annotate(
            total_reads_val=Sum('analytics__total_reads'),
            total_seconds_val=Sum('analytics__total_seconds_read'),
        )
        .order_by('-total_reads_val')
    )
    result = []
    for a in articles:
        result.append({
            'id': a.id,
            'client_id': a.client_id,
            'title': a.title,
            'slug': a.slug,
            'published_at': a.published_at.isoformat() if a.published_at else '',
            'teacher_id': a.author.id if a.author else None,
            'username': a.author.username if a.author else '',
            'first_name': a.author.first_name if a.author else '',
            'last_name': a.author.last_name if a.author else '',
            'display_name': a.author.display_name if a.author else '—',
            'tags': ', '.join(t.name for t in a.tags.all()),
            'total_reads': a.total_reads_val or 0,
            'total_seconds': a.total_seconds_val or 0,
            'word_count': a.word_count,
            'visibility_pct': _visibility(
                a.total_seconds_val or 0, a.total_reads_val or 0, a.word_count or 1200
            ),
        })
    return result


# ---------------------------------------------------------------------------
# Explorateur queries
# ---------------------------------------------------------------------------

def get_raw_events(
    date_str: str = '',
    teacher_id: str = '',
    tag_name: str = '',
    limit: int = 50,
) -> list[dict]:
    qs = (
        ClientActionLog.objects
        .filter(action='article_view', article__isnull=False)
        .select_related('article__author')
    )
    if date_str:
        qs = qs.filter(created_at__date=date_str)
    if teacher_id:
        qs = qs.filter(article__author__id=teacher_id)
    if tag_name:
        qs = qs.filter(article__tags__name=tag_name)

    qs = qs.order_by('-created_at')[:limit]

    result = []
    for al in qs:
        a = al.article
        analytics = ClientArticleAnalytics.objects.filter(article=a).first()
        tr = analytics.total_reads if analytics else 0
        ts = analytics.total_seconds_read if analytics else 0
        wc = a.word_count or 1200
        result.append({
            'id': al.id,
            'section': 'article_view',
            'duration_seconds': 0,
            'created_at': al.created_at.isoformat() if al.created_at else '',
            'article_id': a.id if a else None,
            'article_title': a.title if a else '',
            'teacher_id': a.author.id if a and a.author else None,
            'username': a.author.username if a and a.author else '',
            'first_name': a.author.first_name if a and a.author else '',
            'last_name': a.author.last_name if a and a.author else '',
            'display_name': a.author.display_name if a and a.author else '—',
            'total_reads': tr,
            'total_seconds': ts,
            'word_count': wc,
            'tag_name': ', '.join(a.tags.values_list('name', flat=True)) if a else '',
            'visibility_pct': _visibility(ts, tr, wc),
        })
    return result


def get_bar_chart_data() -> tuple[dict, dict, list[str]]:
    tags = get_all_tags()[:3]
    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven']
    palette = ['#254e70', '#527a55', '#6aaa64']
    bar_data: dict[str, list[int]] = {}
    cat_colors: dict[str, str] = {}

    for i, tag in enumerate(tags):
        bar_data[tag] = [0] * 5
        cat_colors[tag] = palette[i % len(palette)]
        # Count views by day-of-week for this tag
        rows = (
            ClientActionLog.objects
            .filter(action='article_view', article__tags__name=tag)
            .extra(select={'dow': "CAST(strftime('%%w', \"client_actionlog\".\"created_at\") AS INTEGER)"})
            .values('dow')
            .annotate(cnt=Count('id'))
        )
        for r in rows:
            dow = r['dow']  # 0=Sun, 1=Mon ... 6=Sat
            if 1 <= dow <= 5:
                bar_data[tag][dow - 1] += r['cnt']

    return bar_data, cat_colors, days_fr


# ---------------------------------------------------------------------------
# Tendances queries
# ---------------------------------------------------------------------------

def get_tendances_metrics() -> list[dict]:
    articles = (
        ClientArticle.objects
        .filter(status='published', analytics__total_reads__gt=0)
        .select_related('analytics')
        .order_by('-analytics__total_seconds_read')[:6]
    )
    result = []
    for a in articles:
        an = a.analytics
        result.append({
            'id': a.id,
            'title': a.title,
            'total_reads': an.total_reads,
            'total_seconds': an.total_seconds_read,
            'avg_minutes': round(an.total_seconds_read / an.total_reads / 60, 1) if an.total_reads else 0,
        })
    return result


def get_device_breakdown(since: date) -> list[dict]:
    logs = ClientActionLog.objects.filter(
        action='article_view', created_at__date__gte=since
    ).values_list('user_agent', flat=True)
    counts = {'Desktop': 0, 'Mobile': 0, 'Tablet': 0}
    for ua in logs:
        _, _, dev = _parse_ua(ua)
        counts[dev] = counts.get(dev, 0) + 1
    total = sum(counts.values()) or 1
    return [
        {'label': k, 'pct': round(v / total * 100)}
        for k, v in counts.items() if v > 0
    ]


def get_browser_breakdown(since: date) -> list[dict]:
    logs = ClientActionLog.objects.filter(
        created_at__date__gte=since
    ).values_list('user_agent', flat=True)
    counts = {}
    for ua in logs:
        _, br, _ = _parse_ua(ua)
        counts[br] = counts.get(br, 0) + 1
    total = sum(counts.values()) or 1
    return [
        {'label': k, 'pct': round(v / total * 100)}
        for k, v in counts.items() if v > 0
    ]


def get_total_impressions(since: date) -> int:
    return ClientArticleAnalytics.objects.filter(
        article__updated_at__date__gte=since
    ).aggregate(total=Sum('total_reads'))['total'] or 0


def get_retention_pct(since: date) -> int:
    avg = ClientArticleAnalytics.objects.filter(
        total_reads__gt=0, article__updated_at__date__gte=since
    ).aggregate(
        avg_time=Avg(F('total_seconds_read') * 1.0 / F('total_reads'))
    )['avg_time'] or 0
    return min(round(avg / 900 * 100), 100)


# ---------------------------------------------------------------------------
# Author detail queries
# ---------------------------------------------------------------------------

def get_author_detail(pk: int) -> dict | None:
    try:
        user = ClientUser.objects.get(pk=pk)
    except ClientUser.DoesNotExist:
        return None

    articles = ClientArticle.objects.filter(author=user)
    total_articles = articles.count()
    published = articles.filter(status='published').count()

    analytics_qs = ClientArticleAnalytics.objects.filter(article__author=user)
    total_reads = analytics_qs.aggregate(t=Sum('total_reads'))['t'] or 0
    total_seconds = analytics_qs.aggregate(t=Sum('total_seconds_read'))['t'] or 0
    avg_time = round(total_seconds / total_reads, 1) if total_reads else 0

    total_comments = ClientReaderComment.objects.filter(article__author=user).count()
    total_shares = ClientActionLog.objects.filter(
        action='article_share', article__author=user
    ).count()

    # Category distribution
    cat_dist = list(
        articles.filter(status='published').exclude(category='')
        .values('category')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
    )
    for r in cat_dist:
        r['label'] = ClientArticle.CATEGORY_LABELS.get(r['category'], r['category'])

    # Section engagement
    section_totals = analytics_qs.aggregate(
        intro=Sum('intro_seconds'),
        objectives=Sum('objectives_seconds'),
        content=Sum('content_seconds'),
        conclusion=Sum('conclusion_seconds'),
        resources=Sum('resources_seconds'),
    )
    sections = {
        'Introduction': section_totals['intro'] or 0,
        'Objectifs': section_totals['objectives'] or 0,
        'Contenu': section_totals['content'] or 0,
        'Conclusion': section_totals['conclusion'] or 0,
        'Ressources': section_totals['resources'] or 0,
    }
    top_section = max(sections, key=sections.get) if any(sections.values()) else 'Aucune donnée'

    # Article list with analytics
    article_list = []
    for a in articles.select_related('author').order_by('-updated_at'):
        an = ClientArticleAnalytics.objects.filter(article=a).first()
        article_list.append({
            'id': a.id,
            'title': a.title,
            'slug': a.slug,
            'status': a.status,
            'category_label': a.category_label,
            'created_at': a.created_at,
            'total_reads': an.total_reads if an else 0,
            'total_seconds': an.total_seconds_read if an else 0,
            'comment_count': ClientReaderComment.objects.filter(article=a).count(),
        })

    return {
        'user': user,
        'total_articles': total_articles,
        'published': published,
        'total_reads': total_reads,
        'total_seconds': total_seconds,
        'avg_time': avg_time,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'top_section': top_section,
        'sections': sections,
        'category_dist': cat_dist,
        'articles': article_list,
    }


def get_author_daily_reads(pk: int, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientActionLog.objects
        .filter(action='article_view', article__author__id=pk, created_at__date__gte=since)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


# ---------------------------------------------------------------------------
# User activity queries
# ---------------------------------------------------------------------------

def get_all_users_activity() -> list[dict]:
    users = ClientUser.objects.all().order_by('-date_joined')
    result = []
    for u in users:
        article_count = ClientArticle.objects.filter(author=u).count()
        published_count = ClientArticle.objects.filter(author=u, status='published').count()
        comment_count = ClientReaderComment.objects.filter(article__author=u).count()
        total_reads = ClientArticleAnalytics.objects.filter(
            article__author=u
        ).aggregate(t=Sum('total_reads'))['t'] or 0
        total_shares = ClientActionLog.objects.filter(
            action='article_share', article__author=u
        ).count()
        last_activity = ClientActionLog.objects.filter(
            user=u
        ).order_by('-created_at').values_list('created_at', flat=True)[:1]

        result.append({
            'id': u.id,
            'client_id': u.client_id,
            'username': u.username,
            'display_name': u.display_name,
            'email': u.email,
            'date_joined': u.date_joined,
            'last_login': u.last_login,
            'is_active': u.is_active,
            'article_count': article_count,
            'published_count': published_count,
            'comment_count': comment_count,
            'total_reads': total_reads,
            'total_shares': total_shares,
            'last_activity': last_activity[0] if last_activity else None,
        })
    return result


def get_user_actions_daily(days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        ClientActionLog.objects
        .filter(created_at__date__gte=since)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(cnt=Count('id'))
    )
    data = {r['day'].isoformat(): r['cnt'] for r in rows}
    return _fill_days(data, days)


# ---------------------------------------------------------------------------
# Time-period filtered queries
# ---------------------------------------------------------------------------

def get_dashboard_for_period(
    period_type: str,
    period_value: str,
) -> dict:
    """
    Return dashboard data filtered by a time period.

    period_type: 'day' | 'week' | 'month' | 'year'
    period_value:
        day   → '2026-04-10'
        week  → '2026-04-05' (start of week)
        month → '2026-04'
        year  → '2026'
    """
    from datetime import datetime

    if period_type == 'day':
        try:
            d = datetime.strptime(period_value, '%Y-%m-%d').date()
        except ValueError:
            d = date.today()
        start, end = d, d

    elif period_type == 'week':
        try:
            d = datetime.strptime(period_value, '%Y-%m-%d').date()
        except ValueError:
            d = date.today()
        start = d
        end = d + timedelta(days=6)

    elif period_type == 'month':
        try:
            d = datetime.strptime(period_value + '-01', '%Y-%m-%d').date()
        except ValueError:
            d = date.today().replace(day=1)
        start = d
        # Last day of month
        if d.month == 12:
            end = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)

    elif period_type == 'year':
        try:
            y = int(period_value)
        except ValueError:
            y = date.today().year
        start = date(y, 1, 1)
        end = date(y, 12, 31)
    else:
        start = date.today() - timedelta(days=30)
        end = date.today()

    # Filter queries
    views = ClientActionLog.objects.filter(
        action='article_view', created_at__date__gte=start, created_at__date__lte=end
    )
    shares = ClientActionLog.objects.filter(
        action='article_share', created_at__date__gte=start, created_at__date__lte=end
    )
    comments = ClientReaderComment.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    )
    new_articles = ClientArticle.objects.filter(
        status='published', published_at__date__gte=start, published_at__date__lte=end
    )
    new_users = ClientUser.objects.filter(
        date_joined__date__gte=start, date_joined__date__lte=end
    )

    # Daily breakdown within period
    days_count = (end - start).days + 1
    views_daily = {}
    for r in views.annotate(day=TruncDate('created_at')).values('day').annotate(cnt=Count('id')):
        views_daily[r['day'].isoformat()] = r['cnt']

    comments_daily = {}
    for r in comments.annotate(day=TruncDate('created_at')).values('day').annotate(cnt=Count('id')):
        comments_daily[r['day'].isoformat()] = r['cnt']

    articles_daily = {}
    for r in new_articles.annotate(day=TruncDate('published_at')).values('day').annotate(cnt=Count('id')):
        articles_daily[r['day'].isoformat()] = r['cnt']

    # Fill gaps
    def fill(data_dict):
        result = {}
        for i in range(days_count):
            d = (start + timedelta(days=i)).isoformat()
            result[d] = data_dict.get(d, 0)
        return [{'date': k, 'count': v} for k, v in result.items()]

    # Top articles in period
    top_articles = list(
        views
        .filter(article__isnull=False)
        .values('article__title', article_pk=F('article__id'))
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )

    # Top authors in period
    top_authors = list(
        views
        .filter(article__isnull=False, article__author__isnull=False)
        .values('article__author__username', author_pk=F('article__author__id'),
                fn=F('article__author__first_name'), ln=F('article__author__last_name'))
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )
    for a in top_authors:
        full = f"{a.get('fn', '')} {a.get('ln', '')}".strip()
        a['display_name'] = full or a.get('article__author__username', '—')

    return {
        'start': start.isoformat(),
        'end': end.isoformat(),
        'total_views': views.count(),
        'total_shares': shares.count(),
        'total_comments': comments.count(),
        'new_articles': new_articles.count(),
        'new_users': new_users.count(),
        'views_daily': fill(views_daily),
        'comments_daily': fill(comments_daily),
        'articles_daily': fill(articles_daily),
        'top_articles': top_articles,
        'top_authors': top_authors,
    }
