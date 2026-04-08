# Digital Scholar — Serveur analytique

> Tableau de bord analytique qui reçoit, stocke et visualise les données synchronisées depuis le CMS client EduTrack.

---

## Démarrage

```bash
cd serveur
python manage.py migrate
python manage.py runserver 8001
```

Accéder au dashboard : `http://localhost:8001/dashboard/`

---

## Structure de l'application `analytics/`

| Fichier | Rôle | Nomenclature Django |
|---------|------|---------------------|
| `models.py` | 12 modèles (5 legacy + 7 synced `Client*`) | Standard |
| `views.py` | Vues de pages + endpoints legacy | Standard |
| `api.py` | 9 endpoints REST de synchronisation | Convention API |
| `services.py` | Logique métier / requêtes ORM analytiques | Convention services |
| `urls.py` | Routage (pages + API) | Standard |
| `admin.py` | 12 ModelAdmin enregistrés | Standard |
| `apps.py` | Configuration de l'app | Standard |
| `tests.py` | Tests unitaires | Standard |

---

## Modèles synchronisés

Chaque modèle `Client*` est le miroir exact du modèle correspondant côté client. La synchronisation utilise `update_or_create` sur le champ `client_id` (PK du client).

| Modèle | Table | client_id | Champs principaux |
|--------|-------|-----------|-------------------|
| `ClientUser` | `client_user` | PK user | username, email, is_staff, date_joined |
| `ClientTag` | `client_tag` | PK tag | name, slug |
| `ClientArticle` | `client_article` | PK article | title, slug, category, status, author, tags M2M |
| `ClientReaderComment` | `client_readercomment` | PK comment | article, parent, name, message, is_approved |
| `ClientArticleAnalytics` | `client_articleanalytics` | PK analytics | total_reads, total_seconds_read, sections_seconds |
| `ClientAnalyticsEvent` | `client_analyticsevent` | PK event | article, section, duration, session_id |
| `ClientActionLog` | `client_actionlog` | PK log | action, actor_type, user, article, ip, user_agent, payload |

---

## Endpoints de synchronisation (`api.py`)

| Méthode | URL | Corps JSON requis |
|---------|-----|-------------------|
| POST | `/api/sync/user/` | `client_id`, `username`, `email`, `first_name`, `last_name`, `is_staff`, `date_joined` |
| POST | `/api/sync/tag/` | `client_id`, `name`, `slug` |
| POST | `/api/sync/article/` | `client_id`, `author_client_id`, `title`, `slug`, `category`, `status`, ... `tag_ids[]` |
| POST | `/api/sync/article-delete/` | `client_id` |
| POST | `/api/sync/comment/` | `client_id`, `article_client_id`, `parent_client_id`, `name`, `message`, ... |
| POST | `/api/sync/analytics/` | `client_id`, `article_client_id`, `total_reads`, `total_seconds_read`, sections ... |
| POST | `/api/sync/event/` | `client_id`, `article_client_id`, `section`, `duration_seconds`, `session_id` |
| POST | `/api/sync/action-log/` | `client_id`, `action`, `actor_type`, `user_client_id`, `article_client_id`, `payload` |
| POST | `/api/sync/full/` | `users[]`, `tags[]`, `articles[]`, `comments[]`, `article_analytics[]`, `analytics_events[]`, `action_logs[]` |

Réponse : `{"ok": true}` (200) ou `{"ok": false, "error": "..."}` (400/405).

---

## Services analytiques (`services.py`)

Fonctions principales (interrogent les modèles `Client*` via Django ORM) :

| Fonction | Description |
|----------|-------------|
| `get_dashboard_stats()` | KPIs globaux (articles, auteurs, vues, commentaires) |
| `get_article_trend()` | Publication par jour (30 derniers jours) |
| `get_top_articles()` | Top 10 articles par nombre de vues |
| `get_top_categories()` | Répartition par catégorie |
| `get_top_authors()` | Top 10 auteurs par engagement |
| `get_device_stats()` | Répartition OS, navigateurs, appareils |
| `get_article_deep()` | Analytique complète d'un article |
| `get_author_detail()` | Analytique complète d'un auteur |
| `get_all_users_activity()` | Tableau d'activité de tous les utilisateurs |
| `get_dashboard_for_period()` | Dashboard filtré par période (day/week/month/year) |

---

## Pages et navigation

| URL | Nom | Description |
|-----|-----|-------------|
| `/` | `api_docs` | Documentation interactive |
| `/dashboard/` | `dashboard` | Dashboard global + filtre période |
| `/explorateur/` | `explorateur` | Exploration articles |
| `/tendances/` | `tendances` | Tendances |
| `/articles/` | `article_list` | Tous les articles |
| `/articles/<id>/` | `article_detail` | Détail analytique article |
| `/auteurs/` | `auteur_list` | Tous les auteurs |
| `/auteurs/<id>/` | `auteur_detail` | Détail analytique auteur |
| `/utilisateurs/` | `utilisateurs` | Activité utilisateurs |
