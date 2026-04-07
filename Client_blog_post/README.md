# 📚 EduTrack CMS — Application Client

**Plateforme complète de publication pédagogique pour enfants** — Éditeur puissant, suivi analytique détaillé, commentaires threadés, partage avec compteur.

## 🎯 Vue d'ensemble

**EduTrack CMS** est une plateforme moderne de publication d'articles pédagogiques inspirée par **Substack**. Conçue spécifiquement pour les **enseignants et créateurs de contenu éducatif**, elle combine simplicité d'utilisation, design Substack-style responsive, et analytique avancée pour mesurer l'impact des contenus auprès des enfants.

### 🏆 Vision du projet

Offrir une **alternative pédagogique à Substack** : un CMS dédié à la création, publication et diffusion d'articles éducatifs structurés, avec suivi complet de l'engagement des lecteurs (temps de lecture par section, OS/navigateur, appareil, partages, commentaires).

### Caractéristiques principales

✅ **Création d'articles** — Éditeur Substack-style avec sections structurées (introduction, objectifs, contenu, conclusion, ressources)  
✅ **Gestion du contenu** — 20 catégories éducatives + tags libres, statut brouillon/publié  
✅ **Commentaires threadés** — Lecteurs anonymes peuvent commenter et répondre  
✅ **Partage avec tracking** — Compteur de partages, lien copiable  
✅ **Dashboard auteur** — Stats, graphiques, historique articles et commentaires  
✅ **Recherche pondérée** — Multi-champs avec scoring intelligent  
✅ **Analytique intégrée** — Suivi temps de lecture par section, OS/navigateur/appareil  
✅ **Design responsive** — Optimisé mobile et tablette  
✅ **Sécurité** — Sanitisation HTML, protection CSRF, contrôle d'accès  

---

## 🚀 Installation rapide

### Prérequis

- **Python** 3.12+
- **pip** (gestionnaire de paquets Python)
- **SQLite** (inclus avec Python)

### Étapes

```bash
# 1. Cloner le dépôt
git clone <repository_url>
cd "PROJET N°3"

# 2. Créer l'environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
# Sur Windows (PowerShell) :
.\.venv\Scripts\Activate.ps1

# Sur Windows (Command Prompt) :
.venv\Scripts\activate.bat

# Sur macOS/Linux :
source .venv/bin/activate

# 4. Installer les dépendances
pip install django bleach

# 5. Naviguer vers l'app Client
cd Client_blog_post

# 6. Appliquer les migrations
python manage.py migrate

# 7. Créer un superutilisateur (admin)
python manage.py createsuperuser
# → Entrer username, email, mot de passe

# 8. (Optionnel) Charger les données de démonstration
python manage.py seed_demo_data

# 9. Lancer le serveur
python manage.py runserver 8000
```

🌐 **Accès** : http://localhost:8000

---

## 📋 Utilisation

### Flux utilisateur typique

#### 1️⃣ **S'inscrire en tant qu'auteur**
```
http://localhost:8000/accounts/signup/
```
- Entrer : username, prénom, nom, email, mot de passe
- Le compte est créé et vous êtes automatiquement connecté
- Redirection vers le Dashboard

#### 2️⃣ **Créer un article**
```
http://localhost:8000/articles/new/
```
- **Titre** (requis) — le seul champ obligatoire
- **Introduction** — éditeur rich-text Quill
- **Contenu** — section principale enrichie
- **Détails** (dépliable) : catégorie, objectifs, conclusion, questions de réflexion, ressources, tags
- **Image de couverture** — URL ou upload
- **Suivi analytique** — toggle pour envoyer les stats vers le serveur d'analyse
- Cliquer **« Publier »** pour enregistrer

#### 3️⃣ **Publier et promouvoir**
- L'article apparaît immédiatement sur :
  - Page d'accueil (si publié)
  - Page Explorer (recherche et filtres)
  - Dashboard auteur (dans le tableau)
- Les lecteurs peuvent :
  - Lire l'article
  - Le partager (compteur incrémenté)
  - Laisser des commentaires/réponses

#### 4️⃣ **Suivre l'engagement sur le Dashboard**
```
http://localhost:8000/dashboard/
```
- 📊 **Stats** : lectures totales, temps moyen, commentaires, partages
- 📈 **Graphiques** : articles/jour, commentaires/jour, visites/jour, OS/navigateurs/appareils
- 💬 **Commentaires** : articles les plus commentés, commentaires récents
- 📑 **Mes articles** : tableau avec actions (voir/modifier/supprimer)

### Accès publics (visiteur)

#### Page d'accueil
```
http://localhost:8000/
```
- Article vedette (plus récent)
- Grille d'articles récents (max 6)
- Barre de recherche
- Lien vers Explorer

#### Explorer les articles
```
http://localhost:8000/articles/
```
- **Recherche** — filtering par texte (titre, tags, contenu)
- **Catégories** — chips pour filtrer
- **Tags** — cliquables, filtrent les résultats
- **Feed** — liste verticale d'articles

#### Lire un article
```
http://localhost:8000/articles/<slug>/
```
- Contenu structuré (intro, objectifs, contenu, conclusion, ressources)
- Compteur vues/commentaires/partages
- Modal de partage avec copie du lien
- Grille de commentaires threadés (lire + répondre)
- Temps de lecture suivi automatiquement

### Admin Django

```
http://localhost:8000/admin/
```
- Créer/modifier/supprimer articles, commentaires, tags
- Gérer les articles analytics, action logs
- Interface standard Django

---

## 🏗️ Architecture

### Structure du projet

```
Client_blog_post/
├── blog/                          # App Django principale
│   ├── models.py                  # 6 modèles (Article, ReaderComment, ActionLog, etc.)
│   ├── views.py                   # 11 vues
│   ├── forms.py                   # 3 formulaires
│   ├── urls.py                    # Routes
│   ├── admin.py                   # Admin Django
│   ├── templates/blog/            # Templates HTML
│   │   ├── base.html              # Layout principal
│   │   ├── home.html              # Page d'accueil
│   │   ├── article_list.html      # Explorer
│   │   ├── article_detail.html    # Lecture d'article
│   │   ├── article_form.html      # Éditeur
│   │   └── dashboard.html         # Dashboard auteur
│   ├── management/commands/
│   │   └── seed_demo_data.py      # Données de test
│   └── migrations/                # Migrations BD
├── Client_blog_post/              # Config Django projet
│   ├── settings.py                # Configuration
│   ├── urls.py                    # Routes root
│   └── wsgi.py                    # Serveur WSGI
├── static/                        # Fichiers statiques
│   ├── css/                       # Stylesheets
│   │   ├── site.css               # Styles globaux
│   │   ├── home.css
│   │   ├── article_list.css
│   │   ├── article_detail.css
│   │   ├── article_form.css
│   │   ├── dashboard.css
│   │   └── auth.css
│   └── js/
│       └── analytics.js           # Tracking de lecture
├── templates/
│   ├── 404.html                   # Page 404 personnalisée
│   └── registration/              # Pages auth
│       ├── login.html
│       └── signup.html
├── media/                         # Uploads
│   └── articles/images/
├── db.sqlite3                     # Base de données
├── manage.py                      # CLI Django
└── README.md                      # Ce fichier
```

### Modèles de données

| Modèle | Description |
|--------|-------------|
| `User` | Django auth user (auteur ou lecteur) |
| `Article` | Article pédagogique avec sections structurées |
| `Tag` | Tags libres, many-to-many avec Article |
| `ReaderComment` | Commentaires threadés (parent/enfants) |
| `ArticleAnalytics` | Métriques agrégées par article |
| `AnalyticsEvent` | Événements de lecture par section |
| `ActionLog` | Journal d'actions (vues, partages, commentaires) |

### Routes principales

| URL | Méthode | Description |
|-----|---------|-------------|
| `/` | GET | Page d'accueil |
| `/articles/` | GET | Explorer (recherche/filtres) |
| `/articles/new/` | GET, POST | Créer un article (🔒 auth) |
| `/articles/<slug>/` | GET, POST | Lire + commenter |
| `/articles/<slug>/edit/` | GET, POST | Modifier (🔒 auteur) |
| `/articles/<slug>/delete/` | POST | Supprimer (🔒 auteur) |
| `/dashboard/` | GET | Dashboard auteur (🔒 auth) |
| `/analytics/track/` | POST | Webhook tracking (analytics.js) |
| `/analytics/share/` | POST | Tracking partages |
| `/accounts/signup/` | GET, POST | Inscription auteur |
| `/accounts/login/` | GET, POST | Connexion |
| `/accounts/logout/` | GET | Déconnexion |
| `/admin/` | GET, POST | Admin Django |
| `/404/` | GET | Page 404 (test en debug) |

---

## 🔐 Sécurité

### Mesures implémentées

✅ **Sanitisation HTML** — Quill + bleach pour le HTML rich-text  
✅ **CSRF tokens** — Tous les formulaires POST protégés  
✅ **Authentification** — Django auth intégrée, sessions HTTPONLY  
✅ **Contrôle d'accès** — @login_required sur les vues auteur, vérifications ownership  
✅ **Auto-escaping** — Templates Django échappent l'HTML par défaut  
✅ **Validation mots de passe** — Longueur minimale, mots communs bloqués, check similarité  

### À configurer en production

⚠️ **SECRET_KEY** — Générer une nouvelle clé secrète (actuellement hardcodée)  
⚠️ **DEBUG** — Mettre à `False` en production  
⚠️ **ALLOWED_HOSTS** — Configurer les domaines autorisés  
⚠️ **HTTPS** — Forcer redirection HTTP → HTTPS  
⚠️ **Rate limiting** — Ajouter sur les endpoints d'API publics  

---

## 📊 Analytics

### Tracking automatique

L'application suit automatiquement :
- **Lectures** : temps passé par section (Intersection Observer)
- **Partages** : enregistrés quand l'utilisateur copie le lien
- **Commentaires** : actions d'ajout/suppression
- **Vues page** : accès à chaque page

### Logs d'action

Tous les événements sont enregistrés dans `ActionLog` avec :
- Type d'action (view, share, comment, login, logout, etc.)
- Utilisateur (optionnel)
- Article (optionnel)
- Adresse IP
- User-Agent (OS, navigateur, appareil)
- Timestamp
- Payload JSON (données additionnelles)
- Statut de livraison (pending/sent/failed)

### Webhooks vers le serveur d'analyse

Si `enable_analytics=True` sur un article, les logs sont envoyés au serveur Digital Scholar via :
- `POST /api/analytics/` — événements de lecture
- `POST /api/action-log/` — action logs

(Voir `ANALYTICS_ENDPOINT` dans settings.py)

---

## 🧪 Tests

### Exécuter les tests

```bash
python manage.py test
```

### Avec couverture

```bash
pip install coverage
coverage run manage.py test
coverage report --show-missing
```

### Checklist de test complète

Voir le fichier `CHECKLIST_TESTS.html` dans le dossier parent.

---

## ⚙️ Configuration

### Variables d'environnement (optionnel)

Dans `Client_blog_post/settings.py`, vous pouvez configurer :

```python
DEBUG = True                    # Mode debug (False en prod)
SECRET_KEY = '...'             # Clé secrète (générer une nouvelle en prod)
ALLOWED_HOSTS = ['*']          # Domaines autorisés
ANALYTICS_ENDPOINT = '...'     # URL du serveur d'analyse (si enable_analytics)
```

### Limites de fichiers

```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 20_971_520  # 20 MB (corps requête)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10_485_760  # 10 MB (uploads)
```

---

## 📦 Dépendances

```
Django==6.0.3           # Framework web
bleach==6.0.0           # Sanitisation HTML
# Optionnel :
coverage                # Tests avec couverture
pytest-django           # Tests avec pytest
```

Installer toutes les dépendances :
```bash
pip install -r requirements.txt
```

(Si le fichier n'existe pas, utiliser `pip install django bleach`)

---

## 🐛 Debugging

### Erreurs courantes

#### 1️⃣ Module django non trouvé
```
ModuleNotFoundError: No module named 'django'
```
**Solution** : Activer l'environnement virtuel et installer Django
```bash
.\.venv\Scripts\Activate.ps1  # ou source .venv/bin/activate
pip install django bleach
```

#### 2️⃣ Base de données verrouillée (SQLite)
```
database is locked
```
**Solution** : Redémarrer le serveur
```bash
python manage.py runserver 8000
```

#### 3️⃣ Migration non appliquée
```
You have X unapplied migration(s)
```
**Solution** :
```bash
python manage.py migrate
```

#### 4️⃣ Port 8000 déjà utilisé
```
Address already in use
```
**Solution** : Utiliser un autre port
```bash
python manage.py runserver 8001
```

### Logs debug

Activer les logs Django dans settings.py :
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}
```

---

## 📈 Performances

### Optimisations appliquées

✅ Requêtes ORM optimisées (`select_related`, `prefetch_related`, `annotate`)  
✅ Indexe DB sur `category`, `published_at`, `created_at`  
✅ Recherche scoring SQL (pas de calcul Python)  
✅ CDN pour Chart.js et Quill.js  
✅ Caching des compteurs en annotations BD  

### Scalabilité

- **Actuel** : SQLite, ~100 utilisateurs simultanés
- **Recommandé** (50+ articles) : PostgreSQL, Redis, Gunicorn + Nginx
- Voir section **12. Pistes d'amélioration** dans la documentation technique

---

## 🚢 Déploiement

### Production (Gunicorn + Nginx)

```bash
# 1. Installer Gunicorn
pip install gunicorn

# 2. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 3. Lancer Gunicorn
gunicorn Client_blog_post.wsgi:application --bind 0.0.0.0:8000 --workers 4

# 4. Configurer Nginx (proxy reverse, SSL, statiques)
# (Voir documentation Nginx)
```

### Docker (optionnel)

```bash
# Créer une image Docker
docker build -t edutrack-cms .

# Lancer le conteneur
docker run -p 8000:8000 edutrack-cms
```

---

## 📚 Documentation

- **Documentation technique complète** : `DOCUMENTATION_TECHNIQUE.html`
- **Checklist de test** : `CHECKLIST_TESTS.html`
- **Code source** : Voir fichiers `models.py`, `views.py`, `forms.py`

---

## 🤝 Contribution

Les améliorations proposées sont documentées dans la section **12. Pistes d'amélioration** de la documentation technique.

Priorités suggérées :
1. **Pagination** — essentiel dès >50 articles
2. **Modération commentaires** — UI pour approuver/rejeter
3. **Auto-save brouillons** — éviter la perte de contenu
4. **Tests automatisés** — couverture 85%+
5. **Migration PostgreSQL** — pour la concurrence

---

## 📄 Licence

Projet EduTrack CMS — Tous droits réservés.

---

## 📞 Support

Email : support@edutrack.local  
Documenation : Lire le fichier `DOCUMENTATION_TECHNIQUE.html`

---

**Dernière mise à jour** : 7 avril 2026  
**Version** : 1.0.0
