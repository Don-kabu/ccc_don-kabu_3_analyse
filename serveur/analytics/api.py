"""
sync_api.py – API endpoints for receiving synchronised data from the client.

Each endpoint accepts a JSON POST with model data and performs an upsert
(update-or-create) keyed on ``client_id``.

Endpoints:
    POST /api/sync/user/         – Sync a single user
    POST /api/sync/tag/          – Sync a single tag
    POST /api/sync/article/      – Sync a single article (with tags)
    POST /api/sync/comment/      – Sync a single comment
    POST /api/sync/analytics/    – Sync article analytics
    POST /api/sync/event/        – Sync a single analytics event
    POST /api/sync/action-log/   – Sync a single action log
    POST /api/sync/article-delete/ – Delete an article mirror
    POST /api/sync/full/         – Full bulk sync of all data
"""
from __future__ import annotations

import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    ClientActionLog,
    ClientAnalyticsEvent,
    ClientArticle,
    ClientArticleAnalytics,
    ClientReaderComment,
    ClientTag,
    ClientUser,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_body(request):
    return json.loads(request.body.decode('utf-8'))


def _parse_dt(value):
    """Parse an ISO datetime string; return None if empty."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt)
        return dt
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Individual sync endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def sync_user(request):
    """Upsert a ClientUser from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'ok': False, 'error': 'missing client_id'}, status=400)

    obj, created = ClientUser.objects.update_or_create(
        client_id=client_id,
        defaults={
            'username': data.get('username', f'user_{client_id}'),
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'email': data.get('email', ''),
            'is_active': data.get('is_active', True),
            'date_joined': _parse_dt(data.get('date_joined')) or timezone.now(),
            'last_login': _parse_dt(data.get('last_login')),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_tag(request):
    """Upsert a ClientTag from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'ok': False, 'error': 'missing client_id'}, status=400)

    obj, created = ClientTag.objects.update_or_create(
        client_id=client_id,
        defaults={
            'name': data.get('name', ''),
            'slug': data.get('slug', ''),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_article(request):
    """Upsert a ClientArticle from the client (with tag association)."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    author_client_id = data.get('author_id')
    if not client_id:
        return JsonResponse({'ok': False, 'error': 'missing client_id'}, status=400)

    # Resolve author (auto-create stub if needed)
    author = None
    if author_client_id:
        author, _ = ClientUser.objects.get_or_create(
            client_id=author_client_id,
            defaults={
                'username': data.get('author_username', f'user_{author_client_id}'),
                'date_joined': _parse_dt(data.get('created_at')) or timezone.now(),
            },
        )

    if not author:
        return JsonResponse({'ok': False, 'error': 'missing author_id'}, status=400)

    defaults = {
        'author': author,
        'title': data.get('title', ''),
        'slug': data.get('slug', ''),
        'category': data.get('category', ''),
        'intro': data.get('intro', ''),
        'objectives': data.get('objectives', ''),
        'content': data.get('content', ''),
        'conclusion': data.get('conclusion', ''),
        'reflection_questions': data.get('reflection_questions', ''),
        'resources': data.get('resources', ''),
        'illustration_url': data.get('illustration_url', ''),
        'video_url': data.get('video_url', ''),
        'audio_url': data.get('audio_url', ''),
        'enable_analytics': data.get('enable_analytics', True),
        'status': data.get('status', 'draft'),
        'published_at': _parse_dt(data.get('published_at')),
        'created_at': _parse_dt(data.get('created_at')) or timezone.now(),
        'updated_at': _parse_dt(data.get('updated_at')) or timezone.now(),
    }

    obj, created = ClientArticle.objects.update_or_create(
        client_id=client_id,
        defaults=defaults,
    )

    # Associate tags
    tag_ids = data.get('tag_ids', [])
    if tag_ids:
        tags = ClientTag.objects.filter(client_id__in=tag_ids)
        obj.tags.set(tags)
    elif not created:
        pass  # keep existing tags if none supplied on update

    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_article_delete(request):
    """Remove a ClientArticle mirror when it's deleted on the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'ok': False, 'error': 'missing client_id'}, status=400)

    deleted, _ = ClientArticle.objects.filter(client_id=client_id).delete()
    return JsonResponse({'ok': True, 'deleted': deleted > 0})


@csrf_exempt
@require_POST
def sync_comment(request):
    """Upsert a ClientReaderComment from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    article_client_id = data.get('article_id')
    if not client_id or not article_client_id:
        return JsonResponse({'ok': False, 'error': 'missing ids'}, status=400)

    try:
        article = ClientArticle.objects.get(client_id=article_client_id)
    except ClientArticle.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'article not found'}, status=404)

    parent = None
    parent_client_id = data.get('parent_id')
    if parent_client_id:
        parent = ClientReaderComment.objects.filter(client_id=parent_client_id).first()

    obj, created = ClientReaderComment.objects.update_or_create(
        client_id=client_id,
        defaults={
            'article': article,
            'parent': parent,
            'name': data.get('name', 'Lecteur'),
            'email': data.get('email', ''),
            'message': data.get('message', ''),
            'is_approved': data.get('is_approved', True),
            'created_at': _parse_dt(data.get('created_at')) or timezone.now(),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_article_analytics(request):
    """Upsert ClientArticleAnalytics from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    article_client_id = data.get('article_id')
    if not client_id or not article_client_id:
        return JsonResponse({'ok': False, 'error': 'missing ids'}, status=400)

    try:
        article = ClientArticle.objects.get(client_id=article_client_id)
    except ClientArticle.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'article not found'}, status=404)

    obj, created = ClientArticleAnalytics.objects.update_or_create(
        client_id=client_id,
        defaults={
            'article': article,
            'total_reads': data.get('total_reads', 0),
            'total_seconds_read': data.get('total_seconds_read', 0),
            'intro_seconds': data.get('intro_seconds', 0),
            'objectives_seconds': data.get('objectives_seconds', 0),
            'content_seconds': data.get('content_seconds', 0),
            'conclusion_seconds': data.get('conclusion_seconds', 0),
            'resources_seconds': data.get('resources_seconds', 0),
            'updated_at': _parse_dt(data.get('updated_at')) or timezone.now(),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_analytics_event(request):
    """Upsert a ClientAnalyticsEvent from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    article_client_id = data.get('article_id')
    if not client_id or not article_client_id:
        return JsonResponse({'ok': False, 'error': 'missing ids'}, status=400)

    try:
        article = ClientArticle.objects.get(client_id=article_client_id)
    except ClientArticle.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'article not found'}, status=404)

    obj, created = ClientAnalyticsEvent.objects.update_or_create(
        client_id=client_id,
        defaults={
            'article': article,
            'section': data.get('section', ''),
            'duration_seconds': data.get('duration_seconds', 0),
            'session_id': data.get('session_id', ''),
            'created_at': _parse_dt(data.get('created_at')) or timezone.now(),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


@csrf_exempt
@require_POST
def sync_action_log(request):
    """Upsert a ClientActionLog from the client."""
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'ok': False, 'error': 'missing client_id'}, status=400)

    # Resolve optional FKs
    user = None
    user_cid = data.get('user_id')
    if user_cid:
        user = ClientUser.objects.filter(client_id=user_cid).first()

    article = None
    article_cid = data.get('article_id')
    if article_cid:
        article = ClientArticle.objects.filter(client_id=article_cid).first()

    obj, created = ClientActionLog.objects.update_or_create(
        client_id=client_id,
        defaults={
            'action': data.get('action', ''),
            'actor_type': data.get('actor_type', 'anonymous'),
            'user': user,
            'article': article,
            'request_path': data.get('request_path', ''),
            'request_method': data.get('request_method', ''),
            'ip_address': data.get('ip_address', ''),
            'user_agent': (data.get('user_agent', '') or '')[:255],
            'session_id': data.get('session_id', ''),
            'payload': data.get('payload', {}),
            'created_at': _parse_dt(data.get('created_at')) or timezone.now(),
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'id': obj.id})


# ---------------------------------------------------------------------------
# Full bulk sync endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def sync_full(request):
    """
    Receives a full dump of client data and upserts everything.

    Expected JSON body::

        {
            "users":      [ {client_id, username, ...}, ... ],
            "tags":       [ {client_id, name, slug}, ... ],
            "articles":   [ {client_id, author_id, title, ...}, ... ],
            "comments":   [ {client_id, article_id, ...}, ... ],
            "analytics":  [ {client_id, article_id, ...}, ... ],
            "events":     [ {client_id, article_id, ...}, ... ],
            "action_logs": [ {client_id, action, ...}, ... ]
        }
    """
    try:
        data = _json_body(request)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    counts = {}

    # 1) Users
    for u in data.get('users', []):
        cid = u.get('client_id')
        if not cid:
            continue
        ClientUser.objects.update_or_create(
            client_id=cid,
            defaults={
                'username': u.get('username', f'user_{cid}'),
                'first_name': u.get('first_name', ''),
                'last_name': u.get('last_name', ''),
                'email': u.get('email', ''),
                'is_active': u.get('is_active', True),
                'date_joined': _parse_dt(u.get('date_joined')) or timezone.now(),
                'last_login': _parse_dt(u.get('last_login')),
            },
        )
    counts['users'] = len(data.get('users', []))

    # 2) Tags
    for t in data.get('tags', []):
        cid = t.get('client_id')
        if not cid:
            continue
        ClientTag.objects.update_or_create(
            client_id=cid,
            defaults={'name': t.get('name', ''), 'slug': t.get('slug', '')},
        )
    counts['tags'] = len(data.get('tags', []))

    # 3) Articles
    for a in data.get('articles', []):
        cid = a.get('client_id')
        author_cid = a.get('author_id')
        if not cid or not author_cid:
            continue
        author = ClientUser.objects.filter(client_id=author_cid).first()
        if not author:
            continue
        obj, _ = ClientArticle.objects.update_or_create(
            client_id=cid,
            defaults={
                'author': author,
                'title': a.get('title', ''),
                'slug': a.get('slug', ''),
                'category': a.get('category', ''),
                'intro': a.get('intro', ''),
                'objectives': a.get('objectives', ''),
                'content': a.get('content', ''),
                'conclusion': a.get('conclusion', ''),
                'reflection_questions': a.get('reflection_questions', ''),
                'resources': a.get('resources', ''),
                'illustration_url': a.get('illustration_url', ''),
                'video_url': a.get('video_url', ''),
                'audio_url': a.get('audio_url', ''),
                'enable_analytics': a.get('enable_analytics', True),
                'status': a.get('status', 'draft'),
                'published_at': _parse_dt(a.get('published_at')),
                'created_at': _parse_dt(a.get('created_at')) or timezone.now(),
                'updated_at': _parse_dt(a.get('updated_at')) or timezone.now(),
            },
        )
        tag_ids = a.get('tag_ids', [])
        if tag_ids:
            tags = ClientTag.objects.filter(client_id__in=tag_ids)
            obj.tags.set(tags)
    counts['articles'] = len(data.get('articles', []))

    # 4) Comments
    for c in data.get('comments', []):
        cid = c.get('client_id')
        article_cid = c.get('article_id')
        if not cid or not article_cid:
            continue
        article = ClientArticle.objects.filter(client_id=article_cid).first()
        if not article:
            continue
        parent = None
        parent_cid = c.get('parent_id')
        if parent_cid:
            parent = ClientReaderComment.objects.filter(client_id=parent_cid).first()
        ClientReaderComment.objects.update_or_create(
            client_id=cid,
            defaults={
                'article': article,
                'parent': parent,
                'name': c.get('name', 'Lecteur'),
                'email': c.get('email', ''),
                'message': c.get('message', ''),
                'is_approved': c.get('is_approved', True),
                'created_at': _parse_dt(c.get('created_at')) or timezone.now(),
            },
        )
    counts['comments'] = len(data.get('comments', []))

    # 5) Analytics
    for an in data.get('analytics', []):
        cid = an.get('client_id')
        article_cid = an.get('article_id')
        if not cid or not article_cid:
            continue
        article = ClientArticle.objects.filter(client_id=article_cid).first()
        if not article:
            continue
        ClientArticleAnalytics.objects.update_or_create(
            client_id=cid,
            defaults={
                'article': article,
                'total_reads': an.get('total_reads', 0),
                'total_seconds_read': an.get('total_seconds_read', 0),
                'intro_seconds': an.get('intro_seconds', 0),
                'objectives_seconds': an.get('objectives_seconds', 0),
                'content_seconds': an.get('content_seconds', 0),
                'conclusion_seconds': an.get('conclusion_seconds', 0),
                'resources_seconds': an.get('resources_seconds', 0),
                'updated_at': _parse_dt(an.get('updated_at')) or timezone.now(),
            },
        )
    counts['analytics'] = len(data.get('analytics', []))

    # 6) AnalyticsEvents
    for ev in data.get('events', []):
        cid = ev.get('client_id')
        article_cid = ev.get('article_id')
        if not cid or not article_cid:
            continue
        article = ClientArticle.objects.filter(client_id=article_cid).first()
        if not article:
            continue
        ClientAnalyticsEvent.objects.update_or_create(
            client_id=cid,
            defaults={
                'article': article,
                'section': ev.get('section', ''),
                'duration_seconds': ev.get('duration_seconds', 0),
                'session_id': ev.get('session_id', ''),
                'created_at': _parse_dt(ev.get('created_at')) or timezone.now(),
            },
        )
    counts['events'] = len(data.get('events', []))

    # 7) ActionLogs
    for al in data.get('action_logs', []):
        cid = al.get('client_id')
        if not cid:
            continue
        user = None
        if al.get('user_id'):
            user = ClientUser.objects.filter(client_id=al['user_id']).first()
        article = None
        if al.get('article_id'):
            article = ClientArticle.objects.filter(client_id=al['article_id']).first()
        ClientActionLog.objects.update_or_create(
            client_id=cid,
            defaults={
                'action': al.get('action', ''),
                'actor_type': al.get('actor_type', 'anonymous'),
                'user': user,
                'article': article,
                'request_path': al.get('request_path', ''),
                'request_method': al.get('request_method', ''),
                'ip_address': al.get('ip_address', ''),
                'user_agent': (al.get('user_agent', '') or '')[:255],
                'session_id': al.get('session_id', ''),
                'payload': al.get('payload', {}),
                'created_at': _parse_dt(al.get('created_at')) or timezone.now(),
            },
        )
    counts['action_logs'] = len(data.get('action_logs', []))

    return JsonResponse({'ok': True, 'synced': counts})
