# EduTrack CMS — Plateforme éducative Client / Serveur

> Blog pédagogique pour enfants avec synchronisation temps-réel et tableau de bord analytique avancé.

---

## Vue d'ensemble

Le projet est composé de **deux applications Django distinctes** qui communiquent par API REST :

| Composant | Dossier | Port | Rôle |
|-----------|---------|------|------|
| **Client** (CMS) | `Client_blog_post/` | `8000` | Publication, lecture, commentaires, tracking |
| **Serveur** (Analytics) | `serveur/` | `8001` | Réception des données, dashboards analytiques avancés |

### Flux de données

```
┌──────────────────────┐       HTTP POST (JSON)       ┌──────────────────────┐
│   CLIENT (port 8000) │ ──────────────────────────▶  │  SERVEUR (port 8001) │
│                      │                               │                      │
│  blog/views.py       │  ─ signup → sync_user         │  analytics/api.py    │
│                      │  ─ article CRUD → sync_article│                      │
│  blog/sync.py        │  ─ comment → sync_comment     │  analytics/services  │
│  (fire-and-forget)   │  ─ analytics → sync_analytics │  analytics/views.py  │
│                      │  ─ every action → sync_log    │                      │
│                      │  ─ full_sync (bootstrap)      │  → Dashboards        │
└──────────────────────┘                               └──────────────────────┘
```

---

## Démarrage rapide

```bash
# 1. Activer l'environnement virtuel
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 2. Appliquer les migrations (serveur)
cd serveur
python manage.py migrate

# 3. Démarrer le serveur analytique
python manage.py runserver 8001

# 4. Dans un 2e terminal — Démarrer le client
cd Client_blog_post
python manage.py migrate
python manage.py runserver

# 5. (Optionnel) Synchronisation initiale si des données existent déjà
python manage.py full_sync
```

---

## Architecture des fichiers

### Client — `Client_blog_post/`

```
Client_blog_post/
├── manage.py
├── db.sqlite3
├── README_COMPLET.md              ← Documentation détaillée du client
│
├── Client_blog_post/              ← Configuration Django (projet)
│   ├── settings.py                   SERVER_BASE_URL, ANALYTICS_ENDPOINT
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│   └── __init__.py
│
├── blog/                          ← Application principale
│   ├── models.py                     7 modèles (Tag, Article, ReaderComment,
│   │                                 ArticleAnalytics, AnalyticsEvent, ActionLog)
│   ├── views.py                      11 vues (home, CRUD article, dashboard, ...)
│   ├── forms.py                      3 formulaires (ArticleForm, SignupForm, CommentForm)
│   ├── urls.py                       12 routes
│   ├── admin.py                      6 ModelAdmin enregistrés
│   ├── sync.py                    ← MODULE DE SYNCHRONISATION
│   │                                 sync_user(), sync_article(), sync_comment(),
│   │                                 sync_article_analytics(), sync_analytics_event(),
│   │                                 sync_action_log(), sync_article_delete(), full_sync()
│   ├── apps.py
│   ├── tests.py
│   ├── management/
│   │   └── commands/
│   │       ├── seed_demo_data.py     Génère données de démo
│   │       └── full_sync.py          Commande : python manage.py full_sync
│   ├── migrations/
│   └── templates/blog/
│       ├── base.html                 Layout principal
│       ├── home.html                 Page d'accueil (articles vedettes)
│       ├── article_list.html         Explorer / recherche
│       ├── article_detail.html       Lecture + commentaires threadés
│       ├── article_form.html         Éditeur (création / édition)
│       ├── article_delete.html       Confirmation suppression
│       ├── dashboard.html            Tableau de bord auteur (8 graphiques)
│       └── comment_node.html         Partial : commentaire récursif
│
├── templates/                     ← Templates globaux
│   ├── 404.html
│   └── registration/
│       ├── login.html
│       └── signup.html
│
├── static/
│   ├── css/  (7 fichiers)           base, home, article_list, article_detail,
│   │                                 article_form, dashboard, auth
│   └── js/
│       └── analytics.js              Intersection Observer + tracking sections
│
└── media/articles/images/         ← Uploads d'illustrations
```

### Serveur — `serveur/`

```
serveur/
├── manage.py
├── db.sqlite3
│
├── digital_scholar/               ← Configuration Django (projet)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│   └── __init__.py
│
├── analytics/                     ← Application principale
│   ├── models.py                     12 modèles :
│   │                                 ── Legacy (5) : Teacher, Article, ArticleMetrics,
│   │                                    DailyReads, RawEvent
│   │                                 ── Synced (7) : ClientUser, ClientTag, ClientArticle,
│   │                                    ClientReaderComment, ClientArticleAnalytics,
│   │                                    ClientAnalyticsEvent, ClientActionLog
│   ├── views.py                      Vues de pages (dashboard, explorateur, tendances,
│   │                                 articles, auteurs, utilisateurs) + endpoints legacy
│   ├── api.py                     ← ENDPOINTS DE SYNCHRONISATION
│   │                                 POST /api/sync/user/
│   │                                 POST /api/sync/tag/
│   │                                 POST /api/sync/article/
│   │                                 POST /api/sync/article-delete/
│   │                                 POST /api/sync/comment/
│   │                                 POST /api/sync/analytics/
│   │                                 POST /api/sync/event/
│   │                                 POST /api/sync/action-log/
│   │                                 POST /api/sync/full/
│   ├── services.py                ← LOGIQUE MÉTIER (ORM)
│   │                                 Requêtes analytiques : dashboard global,
│   │                                 article détail, auteur détail, activité utilisateurs,
│   │                                 filtrage par période (jour/semaine/mois/année)
│   ├── urls.py                       Routage complet (pages + API sync)
│   ├── admin.py                      12 ModelAdmin (legacy + synced)
│   ├── apps.py
│   ├── tests.py
│   └── migrations/
│
├── templates/
│   ├── base.html                     Layout + sidebar navigation
│   └── analytics/
│       ├── dashboard.html            Dashboard global + filtre par période
│       ├── explorateur.html          Exploration articles
│       ├── tendances.html            Tendances et métriques
│       ├── article_list.html         Liste tous les articles
│       ├── article_detail.html       Analytique détaillée d'un article
│       ├── auteur_list.html          Liste des auteurs + stats
│       ├── auteur_detail.html        Analytique détaillée d'un auteur
│       ├── utilisateurs.html         Activité des utilisateurs
│       ├── api_docs.html             Documentation interactive des endpoints
│       └── registration/login.html
│
├── static/
│   ├── css/  (dashboard.css, site.css)
│   └── js/
│
└── Design/                        ← Maquettes de design (référence)
```

---

## Modèles de données

### Client (`blog/models.py`)

| Modèle | Description | Champs clés |
|--------|-------------|-------------|
| `Tag` | Étiquettes libres | name, slug |
| `Article` | Article pédagogique | title, slug, category (20 choix), intro, content, conclusion, status, published_at, enable_analytics |
| `ReaderComment` | Commentaire threadé | article, parent, name, email, message, is_approved |
| `ArticleAnalytics` | Métriques agrégées | total_reads, total_seconds_read, *_seconds par section |
| `AnalyticsEvent` | Événement unitaire | article, section, duration_seconds, session_id |
| `ActionLog` | Journal d'actions | action, actor_type, user, article, ip_address, user_agent, payload, delivery_status |

### Serveur — Modèles synchronisés (`analytics/models.py`)

| Modèle serveur | Table DB | Miroir de |
|---------------|----------|-----------|
| `ClientUser` | `client_user` | `auth_user` |
| `ClientTag` | `client_tag` | `Tag` |
| `ClientArticle` | `client_article` | `Article` |
| `ClientReaderComment` | `client_readercomment` | `ReaderComment` |
| `ClientArticleAnalytics` | `client_articleanalytics` | `ArticleAnalytics` |
| `ClientAnalyticsEvent` | `client_analyticsevent` | `AnalyticsEvent` |
| `ClientActionLog` | `client_actionlog` | `ActionLog` |

Chaque modèle synchronisé possède un champ `client_id` (identifiant dans la BD client) utilisé comme clé de déduplication dans `update_or_create`.

---

## API de synchronisation

Tous les endpoints sont en `POST`, acceptent du JSON, et répondent `{"ok": true}` ou `{"ok": false, "error": "..."}`.

| Endpoint | Fonction | Déclencheur côté client |
|----------|----------|------------------------|
| `/api/sync/user/` | Créer/MAJ un utilisateur | Inscription (`signup`) |
| `/api/sync/tag/` | Créer/MAJ un tag | Création d'article avec nouveaux tags |
| `/api/sync/article/` | Créer/MAJ un article | Création / édition d'article |
| `/api/sync/article-delete/` | Supprimer un article | Suppression d'article |
| `/api/sync/comment/` | Créer/MAJ un commentaire | Nouveau commentaire lecteur |
| `/api/sync/analytics/` | MAJ métriques agrégées | Chaque événement de tracking |
| `/api/sync/event/` | Créer un événement | Chaque section vue par un lecteur |
| `/api/sync/action-log/` | Créer une entrée de log | Chaque action utilisateur |
| `/api/sync/full/` | Synchronisation complète | `python manage.py full_sync` |

### Exemple de payload (`/api/sync/article/`)

```json
{
  "client_id": 42,
  "author_client_id": 3,
  "title": "Les volcans expliqués",
  "slug": "les-volcans-expliques",
  "category": "sciences_amusantes",
  "status": "published",
  "intro": "...",
  "content": "...",
  "conclusion": "...",
  "objectives": "...",
  "reflection_questions": "...",
  "resources": "",
  "published_at": "2026-04-05T14:30:00+00:00",
  "created_at": "2026-04-04T10:00:00+00:00",
  "tag_ids": [1, 5, 12]
}
```

---

## Pages du serveur analytique

| URL | Vue | Description |
|-----|-----|-------------|
| `/` | `api_docs` | Documentation interactive des endpoints |
| `/dashboard/` | `dashboard` | Dashboard global avec filtrage par période |
| `/explorateur/` | `explorateur` | Exploration articles avec métriques |
| `/tendances/` | `tendances` | Tendances et comparaisons |
| `/articles/` | `article_list` | Liste de tous les articles avec stats |
| `/articles/<id>/` | `article_detail` | Analytique profonde d'un article |
| `/auteurs/` | `auteur_list` | Liste des auteurs avec statistiques |
| `/auteurs/<id>/` | `auteur_detail` | Analytique détaillée d'un auteur |
| `/utilisateurs/` | `utilisateurs` | Tableau d'activité des utilisateurs |

### Filtrage par période (Dashboard)

Le dashboard accepte deux paramètres GET :
- `period_type` : `day`, `week`, `month`, `year`
- `period_value` : date au format adapté

Exemples :
- `?period_type=day&period_value=2026-04-08` → journée du 8 avril 2026
- `?period_type=week&period_value=2026-04-06` → semaine du 6 au 12 avril
- `?period_type=month&period_value=2026-04` → mois d'avril 2026
- `?period_type=year&period_value=2026` → année 2026

---

## Module de synchronisation client (`blog/sync.py`)

Chaque fonction sérialise une instance de modèle et effectue un `POST` JSON vers le serveur. Les appels sont **fire-and-forget** : si le serveur est injoignable, l'erreur est ignorée silencieusement pour ne jamais bloquer l'expérience utilisateur.

| Fonction | Modèle source | Endpoint serveur |
|----------|---------------|-----------------|
| `sync_user(user)` | `auth.User` | `/api/sync/user/` |
| `sync_tag(tag)` | `Tag` | `/api/sync/tag/` |
| `sync_article(article)` | `Article` | `/api/sync/article/` |
| `sync_article_delete(id)` | — | `/api/sync/article-delete/` |
| `sync_comment(comment)` | `ReaderComment` | `/api/sync/comment/` |
| `sync_article_analytics(a)` | `ArticleAnalytics` | `/api/sync/analytics/` |
| `sync_analytics_event(e)` | `AnalyticsEvent` | `/api/sync/event/` |
| `sync_action_log(log)` | `ActionLog` | `/api/sync/action-log/` |
| `full_sync()` | Tous | `/api/sync/full/` |

### Points d'intégration dans `views.py`

```
signup()          → sync_user(user)
article_create()  → sync_article(article)
article_edit()    → sync_article(article)
article_delete()  → sync_article_delete(article_id)
article_detail()  → sync_comment(comment)       [sur POST commentaire]
track_analytics() → sync_article_analytics(analytics)
                  → sync_analytics_event(event)
_log_action()     → sync_action_log(log)         [sur CHAQUE action]
```

---

## Configuration

### Client (`Client_blog_post/settings.py`)

```python
SERVER_BASE_URL = 'http://localhost:8001'      # URL du serveur analytique
ANALYTICS_ENDPOINT = 'https://localhost:8001/track/'
ACTION_LOG_ENDPOINT = ANALYTICS_ENDPOINT
```

### Serveur (`digital_scholar/settings.py`)

```python
# Lancement sur le port 8001
# python manage.py runserver 8001
```

---

## Stack technique

```
Python             3.14+
Django             6.0.3
Base de données    SQLite 3
Graphiques         Chart.js 4
Éditeur texte      Quill.js 1.3.7
Typographie        Google Fonts (Newsreader + Public Sans)
```

---

## Commandes utiles

```bash
# Créer des données de démonstration (client)
python manage.py seed_demo_data

# Créer des données de test sur le serveur (sans passer par l'API)
cd serveur
python manage.py seed_test_data          # ajoute aux données existantes
python manage.py seed_test_data --flush  # supprime puis recrée

# Synchroniser toutes les données vers le serveur
cd Client_blog_post
python manage.py full_sync

# Migrations serveur
cd serveur && python manage.py makemigrations analytics && python manage.py migrate

# Migrations client
cd Client_blog_post && python manage.py makemigrations blog && python manage.py migrate
```

---

## Référence complète des endpoints

### Client — Routes publiques et auteur (`blog/urls.py`)

| Méthode | URL | Vue | Auth | Description |
|---------|-----|-----|------|-------------|
| GET | `/` | `home` | Non | Page d'accueil avec articles vedettes |
| GET/POST | `/signup/` | `signup` | Non | Inscription auteur |
| GET | `/articles/` | `article_list` | Non | Explorer les articles (recherche, filtres) |
| GET/POST | `/articles/new/` | `article_create` | Oui | Créer un article |
| GET/POST | `/articles/<slug>/` | `article_detail` | Non | Lire + commenter |
| GET/POST | `/articles/<slug>/edit/` | `article_edit` | Oui | Modifier un article |
| GET/POST | `/articles/<slug>/delete/` | `article_delete` | Oui | Supprimer un article |
| GET | `/dashboard/` | `author_dashboard` | Oui | Tableau de bord auteur |
| POST | `/analytics/track/` | `track_analytics` | Non | Envoyer événement de lecture (AJAX) |
| POST | `/analytics/share/` | `track_share` | Non | Enregistrer un partage (AJAX) |
| GET | `/accounts/logout/` | `logout_view` | Non | Déconnexion |

### Serveur — Pages analytiques (`analytics/urls.py`)

| Méthode | URL | Vue | Description |
|---------|-----|-----|-------------|
| GET | `/` | `api_docs` | Documentation interactive des endpoints |
| GET | `/dashboard/` | `dashboard` | Dashboard global + filtre par période |
| GET | `/explorateur/` | `explorateur` | Exploration articles avec métriques |
| GET | `/tendances/` | `tendances` | Tendances et comparaisons |
| GET | `/articles/` | `article_list` | Liste de tous les articles avec stats |
| GET | `/articles/<id>/` | `article_detail` | Analytique profonde d'un article |
| GET | `/auteurs/` | `auteur_list` | Liste des auteurs avec statistiques |
| GET | `/auteurs/<id>/` | `auteur_detail` | Analytique détaillée d'un auteur |
| GET | `/utilisateurs/` | `utilisateurs` | Tableau d'activité des utilisateurs |

### Serveur — API Legacy (réception directe depuis le JS client)

| Méthode | URL | Vue | Description |
|---------|-----|-----|-------------|
| POST | `/api/analytics/` | `receive_analytics` | Réception d'événements bruts (RawEvent) |
| POST | `/api/action-log/` | `receive_action_log` | Réception de logs d'actions bruts |

### Serveur — API de synchronisation (`analytics/api.py`)

| Méthode | URL | Fonction | Payload JSON |
|---------|-----|----------|-------------|
| POST | `/api/sync/user/` | `sync_user` | `client_id`, `username`, `email`, `first_name`, `last_name`, `is_staff`, `date_joined` |
| POST | `/api/sync/tag/` | `sync_tag` | `client_id`, `name`, `slug` |
| POST | `/api/sync/article/` | `sync_article` | `client_id`, `author_client_id`, `title`, `slug`, `category`, `status`, `intro`, `content`, `conclusion`, `objectives`, `reflection_questions`, `resources`, `published_at`, `created_at`, `tag_ids[]` |
| POST | `/api/sync/article-delete/` | `sync_article_delete` | `client_id` |
| POST | `/api/sync/comment/` | `sync_comment` | `client_id`, `article_client_id`, `parent_client_id`, `name`, `email`, `message`, `is_approved`, `created_at` |
| POST | `/api/sync/analytics/` | `sync_article_analytics` | `client_id`, `article_client_id`, `total_reads`, `total_seconds_read`, `intro_seconds`, `objectives_seconds`, `content_seconds`, `conclusion_seconds`, `resources_seconds` |
| POST | `/api/sync/event/` | `sync_analytics_event` | `client_id`, `article_client_id`, `section`, `duration_seconds`, `session_id`, `created_at` |
| POST | `/api/sync/action-log/` | `sync_action_log` | `client_id`, `action`, `actor_type`, `user_client_id`, `article_client_id`, `request_path`, `request_method`, `ip_address`, `user_agent`, `session_id`, `payload`, `created_at` |
| POST | `/api/sync/full/` | `sync_full` | `users[]`, `tags[]`, `articles[]`, `comments[]`, `article_analytics[]`, `analytics_events[]`, `action_logs[]` |

**Réponses :**
- Succès : `{"ok": true}` (HTTP 200)
- Erreur de validation : `{"ok": false, "error": "description"}` (HTTP 400)
- Mauvaise méthode : `{"ok": false, "error": "POST required"}` (HTTP 405)

---

## Données de test

### Seed serveur (`python manage.py seed_test_data`)

Le jeu de données de test génère :

| Élément | Quantité | Détails |
|---------|----------|---------|
| Utilisateurs | 5 | Amina Diallo, Léo Martin, Sofia Benali, Jules Dupont, Mariama Sow |
| Tags | 12 | sciences, nature, maths, lecture, emotions, creativite, histoire, ecologie, musique, animaux, jeux, decouverte |
| Articles | 10 | Publiés entre 1 et 90 jours, catégories variées |
| Commentaires | 3-8 par article (~52 total) | Noms et messages réalistes, 90% approuvés |
| Analytics | 1 par article | 20-500 lectures, temps de lecture par section |
| Événements | 10-40 par article (~241 total) | Sections aléatoires, durées variées |
| Action Logs | 50-150 par article (~1188 total) | Vues, partages, recherches, mix OS/navigateur/appareil |

### Seed client (`python manage.py seed_demo_data`)

| Élément | Quantité |
|---------|----------|
| Auteurs | 2 (mot de passe : `DemoPass123!`) |
| Articles | 3 publiés avec tags |
| Commentaires | 2-3 par article |
| Analytics | 1 par article avec sections |

---

## Checklist de tests

### 1. Installation et démarrage

| # | Test | Étapes | Résultat attendu | ✓ |
|---|------|--------|-------------------|---|
| 1.1 | Migrations serveur | `cd serveur && python manage.py migrate` | « No migrations to apply » ou migrations appliquées sans erreur | ☐ |
| 1.2 | Migrations client | `cd Client_blog_post && python manage.py migrate` | Idem | ☐ |
| 1.3 | Démarrage serveur | `python manage.py runserver 8001` | « Starting development server at http://127.0.0.1:8001/ » | ☐ |
| 1.4 | Démarrage client | `python manage.py runserver` | « Starting development server at http://127.0.0.1:8000/ » | ☐ |
| 1.5 | Seed serveur | `python manage.py seed_test_data --flush` | Message de succès avec compteurs | ☐ |
| 1.6 | Seed client | `python manage.py seed_demo_data` | Auteurs et articles créés | ☐ |

### 2. Navigation client (port 8000)

| # | Test | Étapes | Résultat attendu | ✓ |
|---|------|--------|-------------------|---|
| 2.1 | Page d'accueil | Ouvrir `http://localhost:8000/` | Articles vedettes affichés, pas d'erreur 500 | ☐ |
| 2.2 | Explorer articles | Cliquer « Explorer » | Liste paginée, filtres catégorie/tag fonctionnels | ☐ |
| 2.3 | Recherche | Taper un mot dans la barre de recherche | Résultats pertinents classés par score | ☐ |
| 2.4 | Lecture article | Cliquer sur un article | Contenu affiché, sections visibles | ☐ |
| 2.5 | Commentaire | Remplir le formulaire de commentaire et envoyer | « Votre commentaire a bien été enregistré. » | ☐ |
| 2.6 | Réponse commentaire | Cliquer « Répondre » sous un commentaire | Commentaire imbriqué affiché | ☐ |
| 2.7 | Inscription | Aller à `/signup/` et créer un compte | Redirigé vers le dashboard | ☐ |
| 2.8 | Connexion | Se connecter avec `auteur_demo` / `DemoPass123!` | Dashboard affiché | ☐ |
| 2.9 | Créer article | Dashboard → « Nouvel article », remplir et publier | Article visible dans la liste | ☐ |
| 2.10 | Modifier article | Dashboard → cliquer « Modifier » sur un article | Formulaire pré-rempli, modifications sauvegardées | ☐ |
| 2.11 | Supprimer article | Dashboard → cliquer « Supprimer » → confirmer | Article retiré de la liste | ☐ |
| 2.12 | Dashboard auteur | Aller à `/dashboard/` | Graphiques affichés (publications, visites, commentaires) | ☐ |
| 2.13 | Partage | Cliquer le bouton de partage sur un article | Compteur incrémenté, modal de lien affiché | ☐ |

### 3. Navigation serveur (port 8001)

| # | Test | Étapes | Résultat attendu | ✓ |
|---|------|--------|-------------------|---|
| 3.1 | Page d'accueil API | Ouvrir `http://localhost:8001/` | Documentation des endpoints affichée | ☐ |
| 3.2 | Dashboard global | Ouvrir `/dashboard/` | KPIs (articles, auteurs, vues, commentaires), graphiques Chart.js | ☐ |
| 3.3 | Filtre par jour | `/dashboard/?period_type=day&period_value=2026-04-08` | Section « Période » affichée avec stats du jour | ☐ |
| 3.4 | Filtre par semaine | `/dashboard/?period_type=week&period_value=2026-04-06` | Stats de la semaine 6-12 avril | ☐ |
| 3.5 | Filtre par mois | `/dashboard/?period_type=month&period_value=2026-04` | Stats du mois d'avril | ☐ |
| 3.6 | Filtre par année | `/dashboard/?period_type=year&period_value=2026` | Stats de l'année 2026 | ☐ |
| 3.7 | Explorateur | Ouvrir `/explorateur/` | Articles avec métriques | ☐ |
| 3.8 | Tendances | Ouvrir `/tendances/` | Graphiques de tendances | ☐ |
| 3.9 | Liste articles | Ouvrir `/articles/` | Tous les articles avec colonnes stats | ☐ |
| 3.10 | Détail article | Cliquer sur un article | Analytique profonde : vues/jour, sections, device stats | ☐ |
| 3.11 | Liste auteurs | Ouvrir `/auteurs/` | Tableau des auteurs avec articles, vues, commentaires | ☐ |
| 3.12 | Détail auteur | Cliquer sur un auteur | Graphiques par auteur : vues/jour, catégories, articles | ☐ |
| 3.13 | Utilisateurs | Ouvrir `/utilisateurs/` | Tableau d'activité : actions, IPs, user-agents | ☐ |

### 4. Synchronisation Client → Serveur

| # | Test | Étapes | Résultat attendu | ✓ |
|---|------|--------|-------------------|---|
| 4.1 | Sync inscription | Créer un nouveau compte sur le client | `ClientUser` créé côté serveur (vérifier admin `/admin/`) | ☐ |
| 4.2 | Sync article create | Publier un article sur le client | `ClientArticle` créé côté serveur | ☐ |
| 4.3 | Sync article edit | Modifier un article sur le client | `ClientArticle` mis à jour côté serveur | ☐ |
| 4.4 | Sync article delete | Supprimer un article sur le client | `ClientArticle` supprimé côté serveur | ☐ |
| 4.5 | Sync commentaire | Poster un commentaire en tant que lecteur | `ClientReaderComment` créé côté serveur | ☐ |
| 4.6 | Sync analytics | Lire un article (rester 10+ secondes) | `ClientArticleAnalytics` mis à jour | ☐ |
| 4.7 | Sync action log | N'importe quelle action (vue, partage, etc.) | `ClientActionLog` créé | ☐ |
| 4.8 | Full sync | `python manage.py full_sync` | Tous les modèles synchronisés, compteurs cohérents | ☐ |
| 4.9 | Serveur éteint | Arrêter le serveur, faire une action client | Client fonctionne normalement (fire-and-forget) | ☐ |
| 4.10 | Idempotence | Exécuter `full_sync` deux fois | Pas de doublons, update_or_create → mêmes compteurs | ☐ |

### 5. API Sync (tests manuels avec curl/PowerShell)

```powershell
# Test sync user
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/sync/user/" `
  -ContentType "application/json" `
  -Body '{"client_id":999,"username":"test_user","email":"test@test.com","first_name":"Test","last_name":"User","date_joined":"2026-04-08T10:00:00Z"}'

# Test sync article
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/sync/article/" `
  -ContentType "application/json" `
  -Body '{"client_id":999,"author_client_id":999,"title":"Test Article","slug":"test-article","category":"sciences_amusantes","status":"published","intro":"Test intro","content":"Test content","conclusion":"Test conclusion","objectives":"Test objectives","reflection_questions":"","resources":"","tag_ids":[]}'

# Test sync comment
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/sync/comment/" `
  -ContentType "application/json" `
  -Body '{"client_id":999,"article_client_id":999,"name":"Testeur","message":"Commentaire de test","is_approved":true}'

# Test erreur méthode GET
Invoke-RestMethod -Method GET -Uri "http://localhost:8001/api/sync/user/"
# Attendu : {"ok": false, "error": "POST required"}

# Test article delete
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/sync/article-delete/" `
  -ContentType "application/json" `
  -Body '{"client_id":999}'
```

### 6. Admin Django

| # | Test | Étapes | Résultat attendu | ✓ |
|---|------|--------|-------------------|---|
| 6.1 | Admin serveur | Ouvrir `http://localhost:8001/admin/` | Login page, puis liste des 12 modèles | ☐ |
| 6.2 | ClientUser list | Cliquer « Client users » | 5+ utilisateurs listés | ☐ |
| 6.3 | ClientArticle list | Cliquer « Client articles » | 10+ articles listés avec filtre status/category | ☐ |
| 6.4 | ClientActionLog list | Cliquer « Client action logs » | Logs avec filtres action/actor_type | ☐ |
| 6.5 | Admin client | Ouvrir `http://localhost:8000/admin/` | 6 modèles blog enregistrés | ☐ |

---

## Pistes d'amélioration

### Court terme (facile)

| # | Amélioration | Détail |
|---|-------------|--------|
| 1 | **Authentification API par token** | Ajouter un header `Authorization: Bearer <token>` sur les endpoints sync pour sécuriser la communication client-serveur |
| 2 | **Queue d'envoi async** | Remplacer les appels sync fire-and-forget par Celery ou Django-Q pour fiabiliser les retransmissions |
| 3 | **Retry automatique** | Si le serveur est indisponible, sauvegarder le payload et retenter avec backoff exponentiel |
| 4 | **Pagination serveur** | Ajouter la pagination sur les listes articles, auteurs, utilisateurs |
| 5 | **Tests unitaires** | Écrire des `TestCase` Django pour chaque endpoint sync (201/400/405) et chaque fonction `services.py` |
| 6 | **Export CSV/PDF** | Ajouter un bouton d'export sur les dashboards (articles, auteurs, périodes) |

### Moyen terme (modéré)

| # | Amélioration | Détail |
|---|-------------|--------|
| 7 | **WebSocket temps réel** | Utiliser Django Channels pour pousser les stats en temps réel vers le dashboard |
| 8 | **Multi-tenant** | Supporter plusieurs instances client connectées au même serveur analytique |
| 9 | **Cache Redis** | Mettre en cache les requêtes ORM lourdes (dashboard, tendances) avec invalidation sur sync |
| 10 | **Filtres combinés** | Permettre de filtrer par auteur + catégorie + période simultanément |
| 11 | **Alertes** | Notifier (email/Slack) quand un article dépasse un seuil de vues ou un commentaire négatif |
| 12 | **Comparaison A/B** | Comparer les métriques de deux articles ou deux périodes côte à côte |

### Long terme (architecture)

| # | Amélioration | Détail |
|---|-------------|--------|
| 13 | **Migration PostgreSQL** | Remplacer SQLite par PostgreSQL pour supporter la concurrence et les volumes |
| 14 | **API REST complète (DRF)** | Remplacer les vues manuelles par Django REST Framework avec sérialiseurs, viewsets, et documentation Swagger |
| 15 | **Conteneurisation Docker** | Dockeriser les deux services avec `docker-compose` pour simplifier le déploiement |
| 16 | **CI/CD** | GitHub Actions : tests automatiques, lint (ruff/black), déploiement staging |
| 17 | **Monitoring** | Intégrer Sentry pour le suivi des erreurs et Prometheus/Grafana pour les métriques système |
| 18 | **Internationalisation (i18n)** | Supporter l'anglais et l'arabe en plus du français |
