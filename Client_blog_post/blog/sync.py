"""
sync.py – Push local data to the analytics server via HTTP POST.

Each function serialises a model instance and posts it to the
corresponding /api/sync/… endpoint on the server.
All calls are fire-and-forget: if the server is unreachable the
error is silently swallowed so client operations are never blocked.
"""

import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

SERVER = getattr(settings, 'SERVER_BASE_URL', 'http://localhost:8001')


def _post(path, data):
    """POST JSON to the server.  Silently ignores network errors."""
    url = f'{SERVER}{path}'
    body = json.dumps(data, default=str).encode('utf-8')
    req = Request(url, data=body,
                  headers={'Content-Type': 'application/json'},
                  method='POST')
    try:
        urlopen(req, timeout=3)
    except (URLError, OSError, ValueError) as exc:
        logger.debug('sync POST %s failed: %s', url, exc)


# ──────────────────────────── individual sync helpers ─────────────────────

def sync_user(user):
    """Push a User instance to the server."""
    _post('/api/sync/user/', {
        'client_id': user.pk,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
    })


def sync_tag(tag):
    """Push a Tag instance."""
    _post('/api/sync/tag/', {
        'client_id': tag.pk,
        'name': tag.name,
        'slug': tag.slug,
    })


def sync_article(article):
    """Push an Article instance (including its tags)."""
    _post('/api/sync/article/', {
        'client_id': article.pk,
        'author_client_id': article.author_id,
        'title': article.title,
        'slug': article.slug,
        'category': article.category,
        'illustration_url': article.illustration_url,
        'video_url': article.video_url,
        'audio_url': article.audio_url,
        'enable_analytics': article.enable_analytics,
        'intro': article.intro,
        'objectives': article.objectives,
        'content': article.content,
        'conclusion': article.conclusion,
        'reflection_questions': article.reflection_questions,
        'resources': article.resources,
        'status': article.status,
        'published_at': article.published_at.isoformat() if article.published_at else None,
        'created_at': article.created_at.isoformat() if article.created_at else None,
        'updated_at': article.updated_at.isoformat() if article.updated_at else None,
        'tag_ids': list(article.tags.values_list('pk', flat=True)),
    })


def sync_article_delete(article_id):
    """Notify the server that an article was deleted."""
    _post('/api/sync/article-delete/', {
        'client_id': article_id,
    })


def sync_comment(comment):
    """Push a ReaderComment instance."""
    _post('/api/sync/comment/', {
        'client_id': comment.pk,
        'article_client_id': comment.article_id,
        'parent_client_id': comment.parent_id,
        'name': comment.name,
        'email': comment.email,
        'message': comment.message,
        'created_at': comment.created_at.isoformat() if comment.created_at else None,
        'is_approved': comment.is_approved,
    })


def sync_article_analytics(analytics):
    """Push an ArticleAnalytics instance."""
    _post('/api/sync/analytics/', {
        'client_id': analytics.pk,
        'article_client_id': analytics.article_id,
        'total_reads': analytics.total_reads,
        'total_seconds_read': analytics.total_seconds_read,
        'intro_seconds': analytics.intro_seconds,
        'objectives_seconds': analytics.objectives_seconds,
        'content_seconds': analytics.content_seconds,
        'conclusion_seconds': analytics.conclusion_seconds,
        'resources_seconds': analytics.resources_seconds,
    })


def sync_analytics_event(event):
    """Push an AnalyticsEvent instance."""
    _post('/api/sync/event/', {
        'client_id': event.pk,
        'article_client_id': event.article_id,
        'section': event.section,
        'duration_seconds': event.duration_seconds,
        'session_id': event.session_id,
        'created_at': event.created_at.isoformat() if event.created_at else None,
    })


def sync_action_log(log):
    """Push an ActionLog instance."""
    _post('/api/sync/action-log/', {
        'client_id': log.pk,
        'action': log.action,
        'actor_type': log.actor_type,
        'user_client_id': log.user_id,
        'article_client_id': log.article_id,
        'request_path': log.request_path,
        'request_method': log.request_method,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'session_id': log.session_id,
        'payload': log.payload,
        'created_at': log.created_at.isoformat() if log.created_at else None,
    })


# ──────────────────────────── full sync (initial bootstrap) ───────────────

def full_sync():
    """Push every object to the server via the bulk endpoint."""
    User = get_user_model()

    users = []
    for u in User.objects.all():
        users.append({
            'client_id': u.pk,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'is_staff': u.is_staff,
            'date_joined': u.date_joined.isoformat() if u.date_joined else None,
        })

    from .models import Tag, Article, ReaderComment, ArticleAnalytics, AnalyticsEvent, ActionLog

    tags = []
    for t in Tag.objects.all():
        tags.append({'client_id': t.pk, 'name': t.name, 'slug': t.slug})

    articles = []
    for a in Article.objects.prefetch_related('tags').all():
        articles.append({
            'client_id': a.pk,
            'author_client_id': a.author_id,
            'title': a.title,
            'slug': a.slug,
            'category': a.category,
            'illustration_url': a.illustration_url,
            'video_url': a.video_url,
            'audio_url': a.audio_url,
            'enable_analytics': a.enable_analytics,
            'intro': a.intro,
            'objectives': a.objectives,
            'content': a.content,
            'conclusion': a.conclusion,
            'reflection_questions': a.reflection_questions,
            'resources': a.resources,
            'status': a.status,
            'published_at': a.published_at.isoformat() if a.published_at else None,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'updated_at': a.updated_at.isoformat() if a.updated_at else None,
            'tag_ids': list(a.tags.values_list('pk', flat=True)),
        })

    comments = []
    for c in ReaderComment.objects.all():
        comments.append({
            'client_id': c.pk,
            'article_client_id': c.article_id,
            'parent_client_id': c.parent_id,
            'name': c.name,
            'email': c.email,
            'message': c.message,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'is_approved': c.is_approved,
        })

    analytics_list = []
    for an in ArticleAnalytics.objects.all():
        analytics_list.append({
            'client_id': an.pk,
            'article_client_id': an.article_id,
            'total_reads': an.total_reads,
            'total_seconds_read': an.total_seconds_read,
            'intro_seconds': an.intro_seconds,
            'objectives_seconds': an.objectives_seconds,
            'content_seconds': an.content_seconds,
            'conclusion_seconds': an.conclusion_seconds,
            'resources_seconds': an.resources_seconds,
        })

    events = []
    for e in AnalyticsEvent.objects.all():
        events.append({
            'client_id': e.pk,
            'article_client_id': e.article_id,
            'section': e.section,
            'duration_seconds': e.duration_seconds,
            'session_id': e.session_id,
            'created_at': e.created_at.isoformat() if e.created_at else None,
        })

    action_logs = []
    for l in ActionLog.objects.all():
        action_logs.append({
            'client_id': l.pk,
            'action': l.action,
            'actor_type': l.actor_type,
            'user_client_id': l.user_id,
            'article_client_id': l.article_id,
            'request_path': l.request_path,
            'request_method': l.request_method,
            'ip_address': l.ip_address,
            'user_agent': l.user_agent,
            'session_id': l.session_id,
            'payload': l.payload,
            'created_at': l.created_at.isoformat() if l.created_at else None,
        })

    _post('/api/sync/full/', {
        'users': users,
        'tags': tags,
        'articles': articles,
        'comments': comments,
        'article_analytics': analytics_list,
        'analytics_events': events,
        'action_logs': action_logs,
    })
