# 📚 EduTrack CMS — Application Client — Documentation Complète

**Plateforme complète de publication pédagogique pour enfants** — Éditeur puissant, suivi analytique détaillé, commentaires threadés, partage avec compteur.

---

## 🎯 Vue d'ensemble

**EduTrack CMS** est une plateforme moderne de publication d'articles pédagogiques inspirée par **Substack**. Conçue spécifiquement pour les **enseignants et créateurs de contenu éducatif**, elle combine :

- ✅ **Simplicité d'utilisation** — Éditeur intuitif type Substack
- ✅ **Design responsive** — Optimisé pour mobile et tablette
- ✅ **Analytique avancée** — Suivi temps de lecture par section, OS/navigateur/appareil
- ✅ **Engagement mesuré** — Compteur partages, commentaires threadés
- ✅ **Contenu structuré** — 20 catégories éducatives + tags libres
- ✅ **Multilingue UI** — Interface 100% en français

### 🏆 Vision du projet

Offrir une **alternative pédagogique à Substack** : un CMS dédié à la création, publication et diffusion d'articles éducatifs structurés, avec suivi complet de l'engagement des lecteurs.

---

## 📊 Caractéristiques principales

| Fonctionnalité | Description |
|----------------|-------------|
| 📝 **Éditeur Substack-style** | Sections structurées : Introduction, Contenu, Conclusion, Ressources. Rich-text avec Quill.js |
| 🏷️ **Catégorisation** | 20 catégories éducatives prédéfinies + tags libres |
| 💬 **Commentaires threadés** | Lecteurs anon. peuvent commenter et répondre (imbrication infinie) |
| 🔗 **Partage avec tracking** | Compteur de partages, lien copiable via modal |
| 📈 **Dashboard auteur complet** | 8 graphiques Chart.js (stats, tendances, appareils) |
| 🔍 **Recherche intelligente** | Scoring multi-champs (titre×12, tags×10, contenu×6) |
| 📊 **Analytics intégrée** | Temps/section, OS, navigateur, appareil, session |
| 🔐 **Sécurité** | Sanitisation HTML (bleach), CSRF, auth Django, contrôle accès |
| 📱 **Responsive** | Mobile-first, tablette, desktop optimisés |
| 🌍 **Multilingue** | Interface 100% français |

---

## 🏗️ Architecture technique

### Stack technologique

```
Frontend:          HTML5 / CSS3 / JavaScript Vanilla
Rich Text Editor:  Quill.js 1.3.7 (CDN)
Charts:            Chart.js 4.4.4 (CDN)
Typography:        Google Fonts (Newsreader + Public Sans)
Backend:           Django 6.0.3 (Python 3.14)
Database:          SQLite 3 (mono-fichier)
Auth:              Django Sessions (HTTPONLY cookies)
HTML Sanitization: bleach 6.x
```

### Architecture globale

```
┌─────────────────────────────────────────────────────────┐
│  NAVIGATEUR (Visiteur / Auteur)                          │
├─────────────────────────────────────────────────────────┤
│  Pages : Home | Explorer | Lecture | Éditeur | Dashboard│
│  Scripts : analytics.js (Intersection Observer)          │
└────────────────────────────────────────────────────────┬─┘
                        │ HTTP (GET/POST)
                        │
┌───────────────────────▼────────────────────────────────┐
│  APPLICATION CLIENT — Django 6.0.3                     │
│                                                         │
│  app/blog/                                              │
│  ├── models.py (7 modèles)                             │
│  ├── views.py (11 vues)                                │
│  ├── forms.py (3 formulaires)                          │
│  ├── urls.py (12 routes)                               │
│  ├── templates/ (6 pages principales)                  │
│  └── static/ (7 CSS + 1 JS)                            │
│                                                         │
│  Endpoints :                                            │
│  GET  /              → home()                           │
│  GET  /articles/     → article_list()                   │
│  POST /analytics/track/   → track_analytics()           │
│  POST /analytics/share/   → track_share()               │
│  ...                                                    │
└───────────────────────┬────────────────────────────────┘
                        │
             ┌──────────▼──────────┐
             │  db.sqlite3         │
             │  (Client DB)        │
             └─────────────────────┘
```

### Modèles de données (7)

```python
┌─────────────┐
│ User        │  Django auth.user (auteur ou visiteur)
├─────────────┤
│ Article     │  Article pédagogique (structure Substack)
├─────────────┤
│ Tag         │  Tags libres (M:N avec Article)
├─────────────┤
│ ReaderComment│ Commentaires threadés (auto-ref parent)
├─────────────┤
│ ArticleAnalytics│ Métriques agrégées par article
├─────────────┤
│ AnalyticsEvent│ Événements bruts (section, durée)
├─────────────┤
│ ActionLog   │  Journal complet d'actions (tracking)
└─────────────┘
```

---

## 🖼️ Pages principales

### 1️⃣ **HOME** — `/`

**"Publier des articles éducatifs qui captivent les enfants."**

![Screenshot Home Page](./screenshots/01_home.png)

#### Layout

```
┌────────────────────────────────────────┐
│         EduTrack [🔍] [💼] [➕] [-]   │ ← Navbar
├────────────────────────────────────────┤
│                                         │
│   HERO SECTION                          │
│   📌 "Publier des articles éducatifs   │
│       qui captivent les enfants."       │
│                                         │
│   [Recherrer un article...] [🔍]       │ ← Barre recherche
│   [Explorer les articles] ← CTA        │
│                                         │
├────────────────────────────────────────┤
│  FEATURED ARTICLE (Plus récent)        │
│  ┌────────┐  Découverte du monde      │ ← Catégorie badge
│  │ Image  │  "ijifef"                 │ ← Titre
│  │        │  Par katsudarim | 06/04  │ ← Auteur + date
│  │        │  ijifif... (intro tronquée)│
│  └────────┘  👁 3  💬 0  🔗 2         │ ← Stats
│                                         │
├────────────────────────────────────────┤
│  ARTICLES RÉCENTS (Grille 3×2)         │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ Card │ │ Card │ │ Card │          │
│  └──────┘ └──────┘ └──────┘          │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ Card │ │ Card │ │ Card │          │
│  └──────┘ └──────┘ └──────┘          │
│                                         │
│           [Voir tous les articles →]  │
│                                         │
├────────────────────────────────────────┤
│ EduTrack CMS - Publication pédagogique │ ← Footer
│ Lecture libre sans compte              │
└────────────────────────────────────────┘
```

#### Components

- **Hero Section** : Tagline + barre recherche hero + bouton CTA « Explorer les articles »
- **Article vedette** : Image 350px, catégorie badge (fond orangé), titre, auteur + date (format d/m/Y), intro tronquée (300 chars, HTML stripped), stats (vues/commentaires/partages)
- **Grille articles récents** : Max 6 items (excluant hero), même structure
- **Lien footer** : « Voir tous les articles → »

#### Interactivité

- Clic sur article → page de lecture
- Recherche → `/articles/?q=...`
- Clic badge catégorie → `/articles/?category=...`
- Clic badge stats → scroll vers commentaires

---

### 2️⃣ **EXPLORER** — `/articles/`

**"Trouvez des articles pédagogiques par thème, tag ou contenu."**

![Screenshot Explorer Page](./screenshots/03_explorer.png)

#### Layout

```
┌────────────────────────────────────────┐
│         EduTrack [🔍] [💼] [➕] [-]   │
├────────────────────────────────────────┤
│  EXPLORER - Trouvez des articles...    │
│  [🔍 Rechercher...] [Rechercher]      │
│                                         │
│  Catégories : [Toutes] [Histoires] ... │ ← Chips filtres
│                                         │
├────────────────────────────────────────┤
│  FEED D'ARTICLES                        │
│                                         │
│  Découverte du monde                   │ ← Catégorie badge
│  ijifif                                │ ← Titre
│  Par katsudarim | 06/04/2025           │ ← Auteur + date
│  ijifif... (intro 220 chars)           │ ← Intro
│  👁 3  💬 0  🔗 2                      │ ← Stats
│  #maths #lecture                       │ ← Tags cliquables
│        [image 200px ▶]                 │ ← Thumbnail
│                                         │
│  ─────────────────────────────────────── ← Separator
│                                         │
│  Histoires de la vie quotidienne       │
│  fofo sans possoon                     │
│  ... (même structure)                  │
│                                         │
│  ... (autres articles)                 │
│                                         │
└────────────────────────────────────────┘
```

#### Components

- **Barre recherche** : Input text + bouton rechercher + bouton effacer (X, si query active)
- **Chips catégories** : 20 catégories, « Toutes » par défaut, surlignées si actives
- **Feed articles** : Vertical list, par article :
  - Badge catégorie (petit, fond pastel)
  - Titre (clickable)
  - Auteur + date
  - Intro tronquée (220 chars, HTML stripped)
  - Stats (vues/commentaires/partages)
  - Tags avec # (cliquables, filtrent)
  - Thumbnail image 200px (droite)
- **État vide** : "Aucun article ne correspond à votre recherche."

#### Filtres

- **Recherche texte** : Scoring multi-champs (titre×12, tags×10, intro×8, contenu×6)
- **Catégorie** : Select une catégorie → filtre
- **Tags** : Click tag → filtre par tag, tag actif surligné
- **Combinaisons** : Tous les filtres sont indépendants et cumulatifs

---

### 3️⃣ **LIRE UN ARTICLE** — `/articles/<slug>/`

![Screenshot Article Detail Page](./screenshots/04_article-detail.png)

**Expérience de lecture optimisée, commentaires, partage.**

#### Layout

```
┌────────────────────────────────────────┐
│         EduTrack [🔍] [💼] [➕] [-]   │
├────────────────────────────────────────┤
│  ARTICLE PÉDAGOGIQUE                   │ ← Eyebrow
│  Découverte du monde                   │ ← Badge catégorie
│                                         │
│  [Modifier] [Supprimer] (si auteur)    │ ← Actions auteur
│  
│  Fufu sans possoon                     │ ← Title (H1)
│  Par katsudarim | 06/04/2025           │ ← Auteur + date
│  👁 3  💬 0  [Partager 2] ←────────┐   │ ← Stats + share btn
│                                    │
│  ┌──────────────────────────────┐ │
│  │      [IMAGE COUVERTURE]      │ │
│  │       (responsive height)    │ │
│  └──────────────────────────────┘ │
│                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                    │
│  Introduction (H2)                │
│  [Rich HTML content]              │ ← data-section="introduction"
│                                    │
│  Objectifs d'apprentissage (H2)    │
│  • Apprendre x                     │ ← Bullet list
│  • Découvrir y                     │
│                                    │
│  Contenu (H2)                      │
│  [Rich HTML content]               │ ← data-section="contenu"
│                                    │
│  Conclusion (H2)                   │
│  [Rich HTML content]               │ ← data-section="conclusion"
│  
│  Questions de réflexion (H3)       │
│  • Question 1                      │
│  • Question 2                      │
│                                    │
│  Ressources supplémentaires (H2)   │ ← data-section="ressources"
│  • http://...                      │ ← Clickable
│  • http://...                      │
│  #maths #lecture #sciences         │ ← Tag cloud
│                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                    │
│  Commentaires (0)                  │ ← H2 + badge compteur
│                                    │
│  [Laisser un commentaire]          │ ← Form principal
│  Prénom* [_______________]         │
│  Email   [_______________]         │
│  Message* [________________________] │
│           0 / 1000  [Envoyer]      │ ← Compteur + btn
│                                    │
│  [Avatar] mandi strenes            │ ← Comment existant
│  @03h00h3 | "je suis d'accord"    │
│           [Répondre]               │ ← Reply btn
│                                    │
│           └─→ [Form de réponse]    │ ← Reply form inline
│  
│  Aucun commentaire pour le moment. │ ← Empty state
│                                    │
└────────────────────────────────────┘
```

#### Features

- **Sections trackées** : `.track-section` = Intersection Observer enregistre le temps passé
- **Share Modal** : Overlay, champ readonly avec lien, bouton Copier, message feedback (2s)
- **Commentaires threadés** : Parents triés récent-first, enfants imbriqués, avatars colorés (hash-based)
- **Reply forms** : Inline, masqués par défaut, toggle avec « Répondre »
- **Analytics** : POST `/analytics/track/` pour chaque section (durée ≥ 2s)

---

![Screenshot Article Editor](./screenshots/05_article-editor.png)

### 4️⃣ **ÉDITER UN ARTICLE** — `/articles/new/` & `/articles/<slug>/edit/`

**Éditeur Substack-style puissant, tous les champs optionnels sauf titre.**

#### Layout

```
┌────────────────────────────────────────┐
│ [🔙] ... [Brouillon ▼] [Publier]     │ ← Top bar
├────────────────────────────────────────┤
│  Titre de l'article*                   │ ← Required
│  [Full-width input]                    │
│                                         │
│  INTRODUCTION                           │ ← Quill editor
│  ┌─────────────────────────────────────┐│
│  │ [Normal ▼] [B] [I] [U] [H₂] ...     ││ ← Toolbar
│  │                                     ││
│  │ [Type here...]                      ││
│  │                                     ││
│  └─────────────────────────────────────┘│
│                                         │
│  IMAGE DE COUVERTURE                    │
│  [URL ▼] [Upload]                      │ ← Tabs
│  [https://...]                         │
│                                         │
│  CONTENU                                │
│  ┌─────────────────────────────────────┐│
│  │ [Normal ▼] [B] [I] [U] [H₂] ...     ││
│  │                                     ││
│  │ [Commencez à écrire...]             ││
│  │                                     ││
│  └─────────────────────────────────────┘│
│                                         │
│  ▼ Détails de l'article                │ ← Collapsible
│  Catégorie : [--Choisir--▼]           │
│  Objectifs : [Textarea, une ligne/objectif]
│  CONCLUSION : [Quill editor]           │
│  Questions : [Textarea]                │
│  Ressources : [Textarea]               │
│  Tags* : [maths, lecture, sciences]    │ ← CSV
│  Suivi analytique : [Toggle ON]        │
│                                         │
└────────────────────────────────────────┘
```

#### Components

- **Top bar** : Back arrow, statut indicateur (Brouillon/Nouveau), dropdown statut, bouton Publier
- **Tous les champs partagent même structure** :
  - Éditeurs Quill : toolbar standardisée (N/H2/H3, B/I/U/S, listes, link, image, clear)
  - Textareas : placeholder, help text, counters
- **Détails dépliable** : Summary text, ouvre/ferme le panneau
- **Statut dropdown** : Brouillon / Publié
- **Validation** : Titre requis, autres optionnels

#### Logique de sauvegarde

- **Création** : `published_at = now()` si statut=Publié, logs `action=article_created`
- **Modification** : Mise à jour fields changés, logs `action=article_updated`
- **Sanitisation** : HTML bleach → tags whitelist (p, br, strong, em, h2, h3, ul, ol, li, a, img)

---

![Screenshot Author Dashboard](./screenshots/02_dashboard.png)

### 5️⃣ **DASHBOARD AUTEUR** — `/dashboard/` (🔒 auth)

**8 graphiques Chart.js + stats + table articles.**

#### Layout

```
┌────────────────────────────────────────┐
│         EduTrack [🔍] [💼] [➕] [-]   │
├────────────────────────────────────────┤
│  Dashboard auteur                      │
│                                         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│  │ 57   │ │0.0s  │ │  8   │ │  0   ││ ← Stat cards (4)
│  │Lect. │ │Temps │ │Comm. │ │Part. ││
│  └──────┘ └──────┘ └──────┘ └──────┘│
│                                         │
│  ┌──────────────────┐ ┌──────────────┐│
│  │  Suivi analytiq. │ │ Répart.      ││ ← Charts (2 doughnuts)
│  │  □ Analysé 60%   │ │ catégories   ││
│  │  □ Non-anal 40%  │ │              ││
│  └──────────────────┘ └──────────────┘│
│                                         │
│  ┌──────────────────┐ ┌──────────────┐│
│  │  Articles publ.  │ │ Commentaires ││ ← Charts (bars + line, 30j)
│  │  [bar chart]     │ │ [line chart] ││
│  └──────────────────┘ └──────────────┘│
│                                         │
│  ┌──────────────────────────────────┐ │
│  │  Visites d'articles (30j)        │ │ ← Chart (line, full-width)
│  │  [line chart - vert]             │ │
│  └──────────────────────────────────┘ │
│                                         │
│  ┌───────────┐ ┌───────────┐ ┌────┐  │
│  │ OS (30j)  │ │ Nav (30j) │ │App ││ ← Charts (3 multiline)
│  └───────────┘ └───────────┘ └────┘  │
│                                         │
│  APERÇU DES COMMENTAIRES              │
│  ┌─────────────────────────────────────┐│
│  │  Total : 8                          ││
│  │  Plus répondu : 2 réponses (article)││
│  │                                     ││
│  │  Articles + commentés      Récents  ││
│  │  • fofo sans possoon (0)   • Don K: ││
│  │  • kaostico (0)              "j'aime"
│  └─────────────────────────────────────┘│
│                                         │
│  MES ARTICLES                           │
│  ┌────────────────────────────────────┐│
│  │ TITRE | CAT | STATUT | CRE | MAJ  ││
│  ├────────────────────────────────────┤│
│  │ijifif │...│Publié │06Avr│06Avr   ││
│  │       │    │       │     │        ││
│  │ [👁] [✏️] [🗑]     │ Lectures: 0 ││
│  └────────────────────────────────────┘│
│  [Aucun article]  ← empty state         │
│                                         │
└────────────────────────────────────────┘
```

#### Stat Cards (4)

1. **Lectures totales** — Somme tous articles
2. **Temps moyen par lecture** — total_seconds / total_reads
3. **Commentaires totaux** — Count ReaderComments
4. **Partages totaux** — Count ActionLog(action=article_share)

#### Charts (8)

| # | Titre | Type | Données | Couleurs |
|---|-------|------|---------|----------|
| 1 | Suivi analytique | Doughnut | Articles analysés vs non-analysés | #d8703d, #e4ded5 |
| 2 | Répartition catégories | Doughnut | Count par catégorie | 20-color palette |
| 3 | Articles publiés (30j) | Barres | Articles/jour | #d8703d (weekend), #e8c4a8 (weekday) |
| 4 | Commentaires (30j) | Ligne | Commentaires/jour | #4a90d9 |
| 5 | Visites d'articles (30j) | Ligne | Vues/jour | #5cb85c |
| 6 | OS (30j) | Multiline | Windows, macOS, Android, iOS, Linux | 10-color palette |
| 7 | Navigateurs (30j) | Multiline | Edge, Opera, Chrome, Firefox, Safari | 10-color palette |
| 8 | Type d'appareil (30j) | Multiline | Mobile, Tablette, Desktop | 10-color palette |

#### Résumé commentaires

- **Total commentaires** + **Plus répondu** (commentaire avec + de réponses)
- **Articles les plus commentés** (top 5, avec badges counts)
- **Commentaires récents** (top 5, nom + date relative + extrait 120 chars)

#### Tableau des articles

| Colonne | Description |
|---------|-------------|
| Titre | Clickable → article_detail |
| Catégorie | Badge coloré ou « — » |
| Statut | Badge Publié (vert) / Brouillon (gris) |
| Date création | d/m/Y |
| Mise à jour | d/m/Y |
| Lectures | Total vues (from ActionLog) |
| Actions | 👁 (if published), ✏️ (edit), 🗑️ (delete, with confirm) |

---

## 🔐 Sécurité

### Mesures implémentées ✅

| Domaine | Protection | Détails |
|---------|-----------|---------|
| **XSS** | Sanitisation HTML | bleach whitelist (p, strong, em, u, h2, h3, a, img, ul, ol, li, br) |
| **CSRF** | Tokens POST | Django middleware activé, tous les forms protégés |
| **Auth** | Session-based | Django auth, HTTPONLY cookies, logout fonctionnel |
| **Accès** | Contrôle @login_required | Vérification ownership sur edit/delete |
| **Mots de passe** | Validation stricte | Min 8 chars, pas mots communs, check similarité, PBKDF2/bcrypt |
| **Injection BD** | ORM Django | Parameterized queries,pas de SQL brut |
| **Clickjacking** | X-Frame-Options | Django middleware activé |

### ⚠️ À configurer en production

```python
# settings.py (production checklist)
DEBUG = False                      # ❌ Jamais True en prod
SECRET_KEY = os.getenv('SECRET_KEY')  # ✅ Variable d'env
ALLOWED_HOSTS = ['example.com']   # ✅ Vos domaines
SECURE_SSL_REDIRECT = True        # ✅ Force HTTPS
SECURE_HSTS_SECONDS = 31536000    # ✅ HSTS header
SESSION_COOKIE_SECURE = True      # ✅ Cookies HTTPS seulement
CSRF_COOKIE_SECURE = True         # ✅ CSRF cookie HTTPS
```

---

## 📊 Analytics & Tracking

### Événements trackés

| Événement | Déclencheur | Payload |
|-----------|------------|---------|
| `home_view` | Accès `/` | {} |
| `article_view` | Accès article | {actor_type} |
| `article_search` | Recherche | {query, result_count} |
| `article_share` | Copie lien | {actor_type} |
| `article_created` | Publication | {status, title} |
| `article_updated` | Modification | {status, title} |
| `article_deleted` | Suppression | {title, slug} |
| `reader_comment_created` | Nouveau commentaire | {comment_id, name} |
| `author_signup` | Inscription | {username} |
| `author_dashboard_view` | Accès dashboard | {article_count, total_reads} |
| `analytics_tracked` | Lecture par section | {section, duration_seconds} |

### Système de logging (ActionLog)

Chaque action enregistrée avec :
```json
{
  "action": "article_view",
  "actor_type": "reader",
  "user_id": 1,
  "article_id": 42,
  "request_path": "/articles/fufu-sans-possoon/",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "session_id": "abc123xyz",
  "payload": {"os": "Windows", "browser": "Chrome", "device": "Desktop"},
  "delivery_status": "sent",
  "created_at": "2025-04-06T15:30:42Z"
}
```

### Tracking de lecture (analytics.js)

```javascript
// Intersection Observer détecte :
- Section entrante/sortante du viewport (40% visible)
- Enregistre le temps passé (seconds)
- POST /analytics/track/ avec :
  {
    "article_id": 42,
    "section": "contenu",
    "duration_seconds": 45,
    "session_id": "abc123xyz"
  }
```

---

## 🚀 Installation et utilisation

### Prérequis

- Python 3.12+
- pip (Python package manager)
- Git

### Installation (5 min)

```bash
# 1. Cloner
git clone <repo_url>
cd "PROJET N°3"

# 2. Environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. Dépendances
pip install django bleach

# 4. Migrations
cd Client_blog_post
python manage.py migrate

# 5. Superuser
python manage.py createsuperuser
# → Entrer username, email, password

# 6. (Optionnel) Données démo
python manage.py seed_demo_data

# 7. Lancer le serveur
python manage.py runserver 9000
```

**🌐 Accès** : http://localhost:9000

### Flux utilisateur

**Visiteur anonyme :**
1. Accueil → Explorer → Recherche/catégories/tags
2. Lire articles → Commenter/répondre/partager

**Auteur :**
1. S'inscrire → Connexion → Dashboard
2. Créer article → Publier
3. Voir engagement en direct (stats, commentaires)

---

## 📁 Structure du projet

```
Client_blog_post/
├── blog/                                  # App Django
│   ├── models.py                          # 7 modèles
│   ├── views.py                           # 11 vues (home, article_list, etc.)
│   ├── forms.py                           # 3 forms (Article, Signup, Comment)
│   ├── urls.py                            # 12 routes
│   ├── admin.py                           # Admin Django
│   ├── migrations/                        # 5 migrations
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo_data.py          # Données de test
│   └── templates/blog/                    # 6 templates
│       ├── base.html                      # Layout principal
│       ├── home.html                      # Accueil
│       ├── article_list.html              # Explorer
│       ├── article_detail.html            # Lecture
│       ├── article_form.html              # Éditeur
│       ├── article_delete.html            # Confirmation suppression
│       └── dashboard.html                 # Dashboard
│
├── Client_blog_post/                      # Config Django
│   ├── settings.py                        # Configuration
│   ├── urls.py                            # Routes root
│   ├── asgi.py                            # ASGI (production)
│   └── wsgi.py                            # WSGI (production)
│
├── static/                                # Fichiers statiques
│   ├── css/                               # 7 stylesheets
│   │   ├── base.css                       # Styles globaux + navbar
│   │   ├── site.css                       # Reset, variables, composants
│   │   ├── home.css                       # Hero, grille articles
│   │   ├── article_list.css               # Feed, chips filtres
│   │   ├── article_detail.css             # Sections, commentaires, modal
│   │   ├── article_form.css               # Éditeur, Quill styling
│   │   ├── dashboard.css                  # Grille stats, graphiques
│   │   └── auth.css                       # Login, signup
│   └── js/
│       └── analytics.js                   # Tracking Intersection Observer
│
├── templates/                             # Templates globales
│   ├── 404.html                           # Page 404 personnalisée
│   └── registration/
│       ├── login.html                     # Connexion
│       └── signup.html                    # Inscription
│
├── media/                                 # Uploads utilisateur
│   └── articles/
│       └── images/
│
├── db.sqlite3                             # Base de données SQLite
├── manage.py                              # Django CLI
├── README.md                              # Documentation (ce fichier)
└── requirements.txt                       # Dépendances Python
```

---

## 🧪 Tests

### Checklist complète

Voir `CHECKLIST_TESTS.html` dans le dossier parent — 120+ tests couvrant toutes les pages et fonctionnalités.

### Exécuter les tests

```bash
# Tous les tests
python manage.py test

# Avec couverture
pip install coverage
coverage run manage.py test
coverage report --show-missing  # Cible : 85%+
```

---

## 🚢 Déploiement

### Développement

```bash
python manage.py runserver 9000
```

### Production (Gunicorn + Nginx)

```bash
# Collecter statiques
python manage.py collectstatic --noinput

# Lancer Gunicorn
gunicorn Client_blog_post.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60

# Nginx config : proxy reverse + SSL (voir docs)
```

### Docker (optionnel)

```bash
docker build -t edutrack-cms .
docker run -p 9000:8000 edutrack-cms
```

---

## 📚 Documentation supplémentaire

- **Documentation technique** : `DOCUMENTATION_TECHNIQUE.html` (12 sections, architecture complète)
- **Checklist de test** : `CHECKLIST_TESTS.html` (16 sections, 120+ tests)
- **Pistes d'amélioration** : Section 12 de la doc technique (5 catégories : features, UX, technique, sécurité, avanc)

---

## 🎯 Fonctionnalités phares résumées

### Visiteur anonyme
✅ Lire tous les articles sans compte  
✅ Recherche multi-champs + filtres (catégorie, tags)  
✅ Commenter et répondre aux commentaires  
✅ Partager les articles (compteur)  
✅ Voir les stats (vues, commentaires, partages)  

### Auteur authentifié
✅ Dashboard complet avec 8 graphiques  
✅ Éditer articles (titre, 6 sections, image, catégorie, tags)  
✅ Voir l'engagement en direct  
✅ Ajouter/supprime articles  
✅ Suivi analytique détaillé (temps/section, OS, navigateur)  

### Backend
✅ Sanitisation HTML (bleach)  
✅ CSRF protection  
✅ Session auth Django  
✅ Logging actionlog complet  
✅ Support webhooks analytics  
✅ Recherche scoring SQL  
✅ Commentaires threadés auto-ref  

---

## 🐛 Debugging

### Erreurs courantes

#### MIME Type Error (CSS not loading)
```
Refused to apply style from 'http://127.0.0.1:9000/static/css/base.css'
because its MIME type ('text/html') is not supported
```
**Solution** : `DEBUG = True` dans settings.py

#### Port already in use
```
Address already in use
```
**Solution** : Utiliser un autre port
```bash
python manage.py runserver 8001
```

#### Migrations not applied
```
You have X unapplied migration(s)
```
**Solution** :
```bash
python manage.py migrate
```

---

## 📞 Support & Contributions

**Email** : support@edutrack.local  
**Docs** : Lire les fichiers documentation HTML  

**Priorités d'amélioration** (voir doc technique section 12) :
1. Pagination (>50 articles)
2. Modération commentaires
3. Profil auteur public
4. Auto-save brouillons
5. Rate limiting + CAPTCHA

---

**Dernière mise à jour** : 7 avril 2026  
**Version** : 1.0.0  
**État** : ✅ Production-ready (development server)