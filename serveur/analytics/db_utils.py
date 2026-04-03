"""
db_utils.py – Raw SQL helpers to query the client application database.

Uses raw sqlite3 (not Django ORM) to avoid Django's debug-formatter
conflict with SQLite strftime % characters.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _client_path() -> str:
    return str(settings.DATABASES['client']['NAME'])


def _rows(sql: str, params=None) -> list[dict]:
    """Execute *sql* on the client DB; return list of row-dicts."""
    conn = sqlite3.connect(f'file:{_client_path()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params or [])
        if cur.description is None:
            return []
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _scalar(sql: str, params=None):
    """Return the first column of the first row, or None."""
    conn = sqlite3.connect(f'file:{_client_path()}?mode=ro', uri=True)
    try:
        cur = conn.execute(sql, params or [])
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _display(row: dict) -> str:
    """Build a human-readable name from a teacher/user row-dict."""
    full = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    return full or row.get('username', '—')


def _word_count_expr(field: str = 'a.content') -> str:
    """SQLite expression that approximates word count of *field*."""
    return f"(LENGTH({field}) - LENGTH(REPLACE({field}, ' ', '')) + 1)"


def _visibility(total_seconds: int, total_reads: int, word_count: int) -> int:
    """Return an integer visibility percentage (0-100)."""
    if not total_reads:
        return 0
    expected = max(word_count, 1) * 0.25  # 0.25 s per word
    ratio = min((total_seconds / total_reads) / expected, 1.0)
    return round(ratio * 100)


# ---------------------------------------------------------------------------
# Dashboard queries
# ---------------------------------------------------------------------------

def get_total_articles() -> int:
    return _scalar("SELECT COUNT(*) FROM blog_article WHERE status='published'") or 0


def get_total_teachers() -> int:
    return _scalar("SELECT COUNT(DISTINCT author_id) FROM blog_article") or 0


def get_monthly_reads(year: int) -> list[int]:
    """Return a 12-element list of article-view counts (index 0 = January)."""
    rows = _rows(
        """
        SELECT CAST(strftime('%m', created_at) AS INTEGER) AS month,
               COUNT(*) AS reads
        FROM   blog_actionlog
        WHERE  action      = 'article_view'
          AND  strftime('%Y', created_at) = ?
        GROUP  BY month
        """,
        [str(year)],
    )
    monthly = [0] * 12
    for r in rows:
        if r['month']:
            monthly[r['month'] - 1] = r['reads']
    return monthly


def get_top_teacher_week() -> dict | None:
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    rows = _rows(
        """
        SELECT u.id, u.username, u.first_name, u.last_name,
               COUNT(al.id) AS reads
        FROM   blog_actionlog al
        JOIN   blog_article a  ON a.id = al.article_id
        JOIN   auth_user    u  ON u.id = a.author_id
        WHERE  al.action    = 'article_view'
          AND  al.created_at >= ?
        GROUP  BY u.id
        ORDER  BY reads DESC
        LIMIT  1
        """,
        [week_start],
    )
    if rows:
        t = rows[0]
        t['display_name'] = _display(t)
        return t
    # Fallback: teacher with most reads overall
    rows = _rows(
        """
        SELECT u.id, u.username, u.first_name, u.last_name,
               COALESCE(SUM(an.total_reads), 0) AS reads
        FROM   auth_user u
        JOIN   blog_article a     ON a.author_id = u.id
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        GROUP  BY u.id
        ORDER  BY reads DESC
        LIMIT  1
        """,
    )
    if rows:
        t = rows[0]
        t['display_name'] = _display(t)
        return t
    return None


def get_top_articles(limit: int = 5) -> list[dict]:
    rows = _rows(
        """
        SELECT a.id,
               a.title,
               a.slug,
               a.published_at,
               u.id   AS teacher_id,
               u.username,
               u.first_name,
               u.last_name,
               COALESCE(an.total_reads, 0)         AS total_reads,
               GROUP_CONCAT(DISTINCT t.name)        AS tags
        FROM   blog_article             a
        JOIN   auth_user                u   ON u.id = a.author_id
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        LEFT   JOIN blog_article_tags   bat ON bat.article_id = a.id
        LEFT   JOIN blog_tag            t   ON t.id = bat.tag_id
        WHERE  a.status = 'published'
        GROUP  BY a.id
        ORDER  BY total_reads DESC
        LIMIT  ?
        """,
        [limit],
    )
    for r in rows:
        r['display_name'] = _display(r)
    return rows


# ---------------------------------------------------------------------------
# Explorateur queries
# ---------------------------------------------------------------------------

def get_all_teachers() -> list[dict]:
    rows = _rows(
        """
        SELECT u.id, u.username, u.first_name, u.last_name
        FROM   auth_user u
        INNER  JOIN blog_article a ON a.author_id = u.id
        GROUP  BY u.id
        ORDER  BY u.last_name, u.first_name
        """,
    )
    for r in rows:
        r['display_name'] = _display(r)
    return rows


def get_all_tags() -> list[str]:
    rows = _rows(
        """
        SELECT DISTINCT t.name
        FROM   blog_tag            t
        JOIN   blog_article_tags bat ON t.id = bat.tag_id
        ORDER  BY t.name
        """,
    )
    return [r['name'] for r in rows]


def get_raw_events(
    date_str: str = '',
    teacher_id: str = '',
    tag_name: str = '',
    limit: int = 50,
) -> list[dict]:
    """Return recent article-view events from the action log."""
    conditions = ["al.action = 'article_view'", "al.article_id IS NOT NULL"]
    params: list = []

    if date_str:
        conditions.append("DATE(al.created_at) = ?")
        params.append(date_str)

    if teacher_id:
        conditions.append("a.author_id = ?")
        params.append(teacher_id)

    if tag_name:
        conditions.append(
            "EXISTS ("
            "  SELECT 1 FROM blog_article_tags bat"
            "  JOIN blog_tag t2 ON t2.id = bat.tag_id"
            "  WHERE bat.article_id = a.id AND t2.name = ?"
            ")"
        )
        params.append(tag_name)

    params.append(limit)
    where = " AND ".join(conditions)

    rows = _rows(
        f"""
        SELECT al.id,
               'article_view'                     AS section,
               0                                  AS duration_seconds,
               al.created_at,
               a.id                               AS article_id,
               a.title                            AS article_title,
               u.id                               AS teacher_id,
               u.username,
               u.first_name,
               u.last_name,
               COALESCE(an.total_reads, 0)         AS total_reads,
               COALESCE(an.total_seconds_read, 0)  AS total_seconds,
               {_word_count_expr()}                AS word_count,
               GROUP_CONCAT(DISTINCT t.name)       AS tag_name
        FROM   blog_actionlog       al
        JOIN   blog_article          a   ON a.id  = al.article_id
        JOIN   auth_user             u   ON u.id  = a.author_id
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        LEFT   JOIN blog_article_tags bat ON bat.article_id = a.id
        LEFT   JOIN blog_tag          t   ON t.id = bat.tag_id
        WHERE  {where}
        GROUP  BY al.id
        ORDER  BY al.created_at DESC
        LIMIT  ?
        """,
        params,
    )
    for r in rows:
        r['display_name'] = _display(r)
        r['visibility_pct'] = _visibility(
            r['total_seconds'], r['total_reads'], r['word_count'] or 1200
        )
    return rows


def get_bar_chart_data() -> tuple[dict, dict, list[str]]:
    """Returns (bar_data, cat_colors, days_fr).

    bar_data  = { 'Pédagogie': [Mon,Tue,Wed,Thu,Fri], ... }
    cat_colors = { 'Pédagogie': '#254e70', ... }
    """
    tags = get_all_tags()[:3]
    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven']
    palette = ['#254e70', '#527a55', '#6aaa64']
    bar_data: dict[str, list[int]] = {}
    cat_colors: dict[str, str] = {}

    for i, tag in enumerate(tags):
        bar_data[tag] = [0] * 5
        cat_colors[tag] = palette[i % len(palette)]

    for tag in tags:
        # SQLite %w: 0=Sunday, 1=Monday … 6=Saturday
        rows = _rows(
            """
            SELECT CAST(strftime('%w', al.created_at) AS INTEGER) AS dow,
                   COUNT(*) AS cnt
            FROM   blog_actionlog       al
            JOIN   blog_article          a   ON a.id  = al.article_id
            JOIN   blog_article_tags    bat  ON bat.article_id = a.id
            JOIN   blog_tag              t   ON t.id  = bat.tag_id
            WHERE  al.action = 'article_view'
              AND  t.name    = ?
              AND  strftime('%w', al.created_at) BETWEEN '1' AND '5'
            GROUP  BY dow
            """,
            [tag],
        )
        for r in rows:
            dow = r['dow']  # 1=Mon … 5=Fri
            if 1 <= dow <= 5:
                bar_data[tag][dow - 1] += r['cnt']

    return bar_data, cat_colors, days_fr


# ---------------------------------------------------------------------------
# Article list query
# ---------------------------------------------------------------------------

def get_articles_list() -> list[dict]:
    rows = _rows(
        f"""
        SELECT a.id,
               a.title,
               a.slug,
               a.published_at,
               a.status,
               u.id            AS teacher_id,
               u.username,
               u.first_name,
               u.last_name,
               GROUP_CONCAT(DISTINCT t.name) AS tags,
               COALESCE(an.total_reads, 0)         AS total_reads,
               COALESCE(an.total_seconds_read, 0)  AS total_seconds,
               {_word_count_expr()}                AS word_count
        FROM   blog_article             a
        JOIN   auth_user                u   ON u.id = a.author_id
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        LEFT   JOIN blog_article_tags   bat ON bat.article_id = a.id
        LEFT   JOIN blog_tag            t   ON t.id = bat.tag_id
        WHERE  a.status = 'published'
        GROUP  BY a.id
        ORDER  BY total_reads DESC
        """,
    )
    for r in rows:
        r['display_name'] = _display(r)
    return rows


# ---------------------------------------------------------------------------
# Article detail query
# ---------------------------------------------------------------------------

def get_article_detail(article_id: int) -> dict | None:
    rows = _rows(
        f"""
        SELECT a.id,
               a.title,
               a.slug,
               a.published_at,
               a.intro,
               a.content,
               a.conclusion,
               u.id            AS teacher_id,
               u.username,
               u.first_name,
               u.last_name,
               GROUP_CONCAT(DISTINCT t.name)        AS tags,
               COALESCE(an.total_reads, 0)           AS total_reads,
               COALESCE(an.total_seconds_read, 0)    AS total_seconds,
               COALESCE(an.intro_seconds, 0)         AS intro_seconds,
               COALESCE(an.objectives_seconds, 0)    AS objectives_seconds,
               COALESCE(an.content_seconds, 0)       AS content_seconds,
               COALESCE(an.conclusion_seconds, 0)    AS conclusion_seconds,
               COALESCE(an.resources_seconds, 0)     AS resources_seconds,
               {_word_count_expr('a.content')}       AS word_count
        FROM   blog_article             a
        JOIN   auth_user                u   ON u.id = a.author_id
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        LEFT   JOIN blog_article_tags   bat ON bat.article_id = a.id
        LEFT   JOIN blog_tag            t   ON t.id = bat.tag_id
        WHERE  a.id = ?
        GROUP  BY a.id
        """,
        [article_id],
    )
    if not rows:
        return None
    r = rows[0]
    r['teacher_display'] = _display(r)
    r['avg_minutes'] = (
        round(r['total_seconds'] / r['total_reads'] / 60, 1)
        if r['total_reads'] else 0
    )
    r['visibility_pct'] = _visibility(
        r['total_seconds'], r['total_reads'], r['word_count'] or 1200
    )
    return r


def get_article_last7_reads(article_id: int) -> tuple[list[int], list[str]]:
    """Returns (reads_per_day[7], day_labels[7]) from action_log for the last 7 days."""
    days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    last7 = []
    labels = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        count = _scalar(
            """
            SELECT COUNT(*) FROM blog_actionlog
            WHERE article_id = ? AND action = 'article_view'
              AND DATE(created_at) = ?
            """,
            [article_id, d.isoformat()],
        ) or 0
        last7.append(count)
        labels.append(days_fr[d.weekday()])
    return last7, labels


# ---------------------------------------------------------------------------
# Tendances queries
# ---------------------------------------------------------------------------

def get_tendances_metrics() -> list[dict]:
    """Average exposition time per article, top 6 by total time."""
    return _rows(
        """
        SELECT a.id,
               a.title,
               COALESCE(an.total_reads, 0)          AS total_reads,
               COALESCE(an.total_seconds_read, 0)   AS total_seconds,
               CASE
                 WHEN COALESCE(an.total_reads, 0) > 0
                 THEN ROUND(
                        CAST(an.total_seconds_read AS REAL) / an.total_reads / 60.0, 1
                      )
                 ELSE 0
               END AS avg_minutes
        FROM   blog_article             a
        LEFT   JOIN blog_articleanalytics an ON an.article_id = a.id
        WHERE  a.status = 'published'
          AND  COALESCE(an.total_reads, 0) > 0
        ORDER  BY total_seconds DESC
        LIMIT  6
        """,
    )


def get_device_breakdown(since: date) -> list[dict]:
    """Derive device distribution from action_log user_agent strings."""
    rows = _rows(
        """
        SELECT user_agent, COUNT(*) AS cnt
        FROM   blog_actionlog
        WHERE  action      = 'article_view'
          AND  created_at >= ?
        GROUP  BY user_agent
        """,
        [since.isoformat()],
    )
    counts = {'Desktop': 0, 'Mobile': 0, 'Tablet': 0}
    for r in rows:
        ua = (r['user_agent'] or '').lower()
        if 'tablet' in ua or 'ipad' in ua:
            counts['Tablet'] += r['cnt']
        elif 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            counts['Mobile'] += r['cnt']
        else:
            counts['Desktop'] += r['cnt']
    total = sum(counts.values()) or 1
    return [
        {'label': k, 'pct': round(v / total * 100)}
        for k, v in counts.items()
        if v > 0
    ]


def get_browser_breakdown(since: date) -> list[dict]:
    rows = _rows(
        """
        SELECT user_agent, COUNT(*) AS cnt
        FROM   blog_actionlog
        WHERE  created_at >= ?
        GROUP  BY user_agent
        """,
        [since.isoformat()],
    )
    counts = {'Chrome': 0, 'Safari': 0, 'Firefox': 0}
    for r in rows:
        ua = (r['user_agent'] or '').lower()
        if 'firefox' in ua:
            counts['Firefox'] += r['cnt']
        elif 'safari' in ua and 'chrome' not in ua:
            counts['Safari'] += r['cnt']
        else:
            counts['Chrome'] += r['cnt']
    total = sum(counts.values()) or 1
    return [
        {'label': k, 'pct': round(v / total * 100)}
        for k, v in counts.items()
        if v > 0
    ]


def get_total_impressions(since: date) -> int:
    return _scalar(
        """
        SELECT COALESCE(SUM(an.total_reads), 0)
        FROM   blog_articleanalytics an
        JOIN   blog_article a ON a.id = an.article_id
        WHERE  a.updated_at >= ?
        """,
        [since.isoformat()],
    ) or 0


def get_retention_pct(since: date) -> int:
    """Retention estimated from average read time vs. 15-min reference."""
    avg = _scalar(
        """
        SELECT AVG(CAST(an.total_seconds_read AS REAL) / NULLIF(an.total_reads, 0))
        FROM   blog_articleanalytics an
        JOIN   blog_article a ON a.id = an.article_id
        WHERE  an.total_reads > 0
          AND  a.updated_at >= ?
        """,
        [since.isoformat()],
    ) or 0
    return min(round(avg / 900 * 100), 100)
