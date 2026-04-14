# Digital Scholar — Présentation Globale du Système

> **Plateforme pédagogique intégrée** — Un système complet de publication, de suivi analytique et de gestion d'articles éducatifs pour enfants.

![Python](https://img.shields.io/badge/Python-3.14+-blue) ![Django](https://img.shields.io/badge/Django-6.0.3-darkgreen)

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Captures d'écran — Client](#captures-décran--client-edutrack)
3. [Captures d'écran — Serveur](#captures-décran--serveur-digital-scholar)
4. [Architecture globale](#architecture-globale)
5. [Stack technologique](#stack-technologique)
6. [Guide de démarrage](#guide-de-démarrage)
7. [Référence des pages et endpoints](#référence-des-pages-et-endpoints)

---

## Vue d'ensemble

**Digital Scholar** est une plateforme éducative composée de deux applications Django qui communiquent par API REST :

| Composant | Dossier | Port | Rôle |
|---|---|---|---|
| **Client — EduTrack CMS** | `Client_blog_post/` | `8000` | Publication, lecture, commentaires, tracking |
| **Serveur — Digital Scholar** | `serveur/` | `8001` | Réception des données, dashboards analytiques |

### Objectifs

- Offrir un **CMS intuitif** pour la création et publication d'articles pédagogiques structurés
- Implémenter un **système d'analytics avancé** pour mesurer l'engagement des lecteurs
- Synchroniser les données en **temps quasi-réel** entre client et serveur
- Proposer des **dashboards intuitifs** avec visualisations de données (Chart.js)

### Cas d'usage

| Utilisateur | Tâches principales |
|---|---|
| **Auteur / Enseignant** | Créer, publier, éditer articles • Visualiser statistiques personnelles • Gérer commentaires |
| **Enfant / Lecteur** | Découvrir et lire des articles • Commenter • Partager |
| **Administrateur** | Exploiter les données analytiques • Analyser tendances • Surveiller l'activité |

---

## Captures d'écran — Client (EduTrack)

### Page d'accueil

Articles vedettes, barre de recherche et articles récents avec compteurs de vues, commentaires et partages :

![Page d'accueil EduTrack](PROJET_04_KABU_DIANZAMBI_DON/client/client%20Accueil.png)

---

### Connexion auteur

Page de connexion réservée aux auteurs pour accéder aux fonctionnalités de publication :

![Connexion auteur](PROJET_04_KABU_DIANZAMBI_DON/client/client%20connexion.png)

---

### Inscription auteur

Formulaire de création de compte auteur (username, prénom, nom, email, mot de passe) :

![Inscription auteur](PROJET_04_KABU_DIANZAMBI_DON/client/client%20register.png)

---

### Explorateur d'articles

Catalogue complet avec filtres par catégorie, recherche plein-texte, statistiques par article et tags :

![Explorateur articles](PROJET_04_KABU_DIANZAMBI_DON/client/client%20Explorer.png)

---

### Lecture d'article

Interface de lecture avec sections structurées (Introduction, Objectifs, Contenu, Conclusion, Ressources), système de commentaires threadés et tracking automatique :

![Lecture d'article](PROJET_04_KABU_DIANZAMBI_DON/client/client%20lecture%20article.png)

---

### Dashboard auteur

Tableau de bord personnel avec KPIs (lectures, temps moyen, commentaires, partages), graphiques de publications/vues/commentaires sur 30 jours, répartition par catégorie, suivi des appareils/navigateurs et liste des articles :

![Dashboard auteur](PROJET_04_KABU_DIANZAMBI_DON/client/client%20dashboard.png)

---

## Captures d'écran — Serveur (Digital Scholar)

### Connexion administrateur

Page de connexion pour accéder au tableau de bord analytique :

![Connexion Digital Scholar](PROJET_04_KABU_DIANZAMBI_DON/serveur/serveur%20connexion.png)

---

### Tableau de bord analytique global

Dashboard principal avec KPIs globaux (vues totales, temps de lecture, commentaires, partages), graphiques tendances publication/vues/commentaires/appareils, top articles (plus vus, commentés, partagés) et tableau de tous les articles :

![Tableau de bord analytique](PROJET_04_KABU_DIANZAMBI_DON/serveur/serveur%20dash.png)

---

### Statistiques articles

Vue d'ensemble des articles : compteurs total/publiés/brouillons/supprimés, répartition par catégorie (donut), répartition par auteur (barres horizontales), tendance de publication sur 30 jours, top 5 articles les plus vus et plus commentés, tableau complet :

![Statistiques articles](PROJET_04_KABU_DIANZAMBI_DON/serveur/serveur%20arcticles.png)

---

### Analyse détaillée d'un article

Analytique profonde par article : vues totales, commentaires, taux d'engagement, partages, âge de l'article depuis sa création, tendance des vues sur 30 jours, progression sur 7 jours et analyse des mots-clés fréquents :

![Analyse article](PROJET_04_KABU_DIANZAMBI_DON/serveur/serveur%20article.jpg)

---

### Documentation API

Documentation interactive des 9 endpoints de synchronisation avec exemples de payload :

![Documentation API](PROJET_04_KABU_DIANZAMBI_DON/serveur/serveur%20Documentation%20API.png)

---

## Architecture globale

```
┌──────────────────────────┐    HTTP POST (JSON)    ┌──────────────────────────┐
│  CLIENT — Port 8000      │ ──────────────────────▶│  SERVEUR — Port 8001     │
│  EduTrack CMS            │                        │  Digital Scholar         │
│                          │  /api/sync/user/        │                          │
│  blog/views.py           │  /api/sync/article/     │  analytics/api.py        │
│  blog/sync.py            │  /api/sync/comment/     │  analytics/services.py   │
│  (fire-and-forget)       │  /api/sync/action-log/  │  analytics/views.py      │
│                          │  /api/sync/full/        │                          │
│  SQLite (client DB)      │                        │  SQLite (server DB)      │
└──────────────────────────┘                        └──────────────────────────┘
```

### Structure du projet

```
PROJET N°3/
│
├── README.md                             ← Documentation technique complète
├── PRESENTATION.md                       ← Ce fichier
│
├── .venv/                                ← Environnement virtuel Python partagé
│
├── Client_blog_post/                     ← APPLICATION CLIENT
│   ├── manage.py
│   ├── db.sqlite3
│   ├── blog/
│   │   ├── models.py                     ← 6 modèles (Tag, Article, ReaderComment, ...)
│   │   ├── views.py                      ← 11 vues (CRUD, auth, tracking)
│   │   ├── forms.py
│   │   ├── sync.py                       ← Synchronisation vers le serveur
│   │   ├── urls.py
│   │   └── management/commands/
│   │       ├── full_sync.py              ← Bootstrap sync
│   │       └── seed_demo_data.py
│   ├── templates/blog/
│   ├── static/css/                       ← 7 feuilles de style
│   └── static/js/analytics.js           ← Tracking Intersection Observer
│
├── serveur/                              ← APPLICATION SERVEUR
│   ├── manage.py
│   ├── db.sqlite3
│   ├── analytics/
│   │   ├── models.py                     ← 12 modèles (5 legacy + 7 Client*)
│   │   ├── views.py                      ← Dashboard, articles, utilisateurs
│   │   ├── api.py                        ← 9 endpoints REST de synchronisation
│   │   ├── services.py                   ← Logique analytique / requêtes ORM
│   │   └── urls.py
│   └── templates/analytics/             ← dashboard, article_list, article_detail,
│                                            utilisateurs, api_docs
│
└── PROJET_04_KABU_DIANZAMBI_DON/        ← Captures d'écran et rapport
    ├── client/                           ← Captures de l'application client
    └── serveur/                          ← Captures de l'application serveur
```

---

## Stack technologique

| Couche | Technologie | Usage |
|---|---|---|
| **Langage** | Python 3.14+ | Backend |
| **Framework** | Django 6.0.3 | Web + ORM |
| **Base de données** | SQLite 3 | Persistance (développement) |
| **Graphiques** | Chart.js 4.4.4 | Dashboards interactifs |
| **Éditeur rich-text** | Quill.js 1.3.7 | Rédaction articles |
| **Tracking** | Intersection Observer API | Suivi lecture par section |
| **Sécurité** | CSRF, sessions Django, PBKDF2, ORM | Protection XSS/injection SQL |
| **Polices** | Google Fonts (Newsreader, Public Sans) | Typographie |

---

## Guide de démarrage

### Prérequis

- Python 3.14+
- L'environnement virtuel est déjà créé dans `.venv/`

---

### 1. Activer l'environnement virtuel

L'environnement virtuel se trouve dans :
```
C:\Users\HP\Documents\CCC\PROJET N°3\.venv
```

```bash
# Depuis la racine PROJET N°3

# Windows — PowerShell
.\.venv\Scripts\Activate.ps1

# Windows — CMD
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

> Le prompt du terminal doit afficher `(.venv)` une fois activé.

---

### 2. Démarrer le SERVEUR analytique (port 8001)

```bash
cd serveur

# Appliquer les migrations
python manage.py migrate

# (Optionnel) Charger des données de test
python manage.py seed_test_data

# Démarrer
python manage.py runserver 8001
```

Accéder au dashboard : **http://localhost:8001/dashboard/**

---

### 3. Démarrer le CLIENT (dans un 2e terminal)

```bash
# Réactiver le .venv si nécessaire
.\.venv\Scripts\Activate.ps1

cd Client_blog_post

# Appliquer les migrations
python manage.py migrate

# (Optionnel) Charger des données de démo
python manage.py seed_demo_data

# Démarrer
python manage.py runserver 8000
```

Accéder au client : **http://localhost:8000/**

---

### 4. Synchroniser les données existantes

Si des données existent côté client et doivent être envoyées au serveur :

```bash
# Dans le terminal client (avec .venv actif)
cd Client_blog_post
python manage.py full_sync
```

---

### Accès rapide

| Page | URL | Description |
|---|---|---|
| **Accueil client** | http://localhost:8000/ | Articles publiés |
| **Connexion auteur** | http://localhost:8000/accounts/login/ | Espace auteur |
| **Inscription auteur** | http://localhost:8000/accounts/signup/ | Créer un compte |
| **Dashboard auteur** | http://localhost:8000/dashboard/ | Statistiques personnelles |
| **Explorateur articles** | http://localhost:8000/articles/ | Tous les articles |
| **Dashboard analytique** | http://localhost:8001/dashboard/ | Analytics globales |
| **Statistiques articles** | http://localhost:8001/articles/ | Stats par article |
| **Statistiques utilisateurs** | http://localhost:8001/utilisateurs/ | Activité utilisateurs |
| **Documentation API** | http://localhost:8001/ | Endpoints de sync |
| **Admin client** | http://localhost:8000/admin/ | Django Admin client |
| **Admin serveur** | http://localhost:8001/admin/ | Django Admin serveur |

### Credentials de démo

```
Username : demo_author   |   Password : DemoPass123!
Username : auteur_demo   |   Password : DemoPass123!
```

---

## Référence des pages et endpoints

### Client — Routes

| Méthode | URL | Description |
|---|---|---|
| GET | `/` | Page d'accueil |
| GET/POST | `/accounts/signup/` | Inscription auteur |
| GET/POST | `/accounts/login/` | Connexion auteur |
| GET | `/articles/` | Explorateur articles |
| GET/POST | `/articles/new/` | Créer un article |
| GET/POST | `/articles/<slug>/` | Lire + commenter |
| GET/POST | `/articles/<slug>/edit/` | Modifier un article |
| GET/POST | `/articles/<slug>/delete/` | Supprimer un article |
| GET | `/dashboard/` | Dashboard auteur |
| POST | `/analytics/track/` | Tracking section (AJAX) |
| POST | `/analytics/share/` | Enregistrer partage (AJAX) |

### Serveur — Pages analytiques

| Méthode | URL | Description |
|---|---|---|
| GET | `/` | Documentation API |
| GET | `/dashboard/` | Dashboard global |
| GET | `/articles/` | Statistiques articles |
| GET | `/articles/<id>/` | Analyse détaillée article |
| GET | `/utilisateurs/` | Activité utilisateurs |

### Serveur — API de synchronisation

| Endpoint | Déclencheur côté client |
|---|---|
| `POST /api/sync/user/` | Inscription |
| `POST /api/sync/tag/` | Création article avec nouveaux tags |
| `POST /api/sync/article/` | Création / édition article |
| `POST /api/sync/article-delete/` | Suppression article |
| `POST /api/sync/comment/` | Nouveau commentaire |
| `POST /api/sync/analytics/` | Événement de lecture par section |
| `POST /api/sync/event/` | Événement analytics unitaire |
| `POST /api/sync/action-log/` | Chaque action (vue, partage, commentaire, ...) |
| `POST /api/sync/full/` | `python manage.py full_sync` |

---

## Fonctionnalités principales

### Application CLIENT

- Authentification auteurs (Signup / Login / Logout)
- CRUD articles structurés (20 catégories + tags libres)
- Éditeur Rich-text Quill.js avec support images, vidéos, audio
- Système de commentaires threadés (réponses imbriquées)
- Tracking analytics par section (Intersection Observer API)
- Dashboard auteur avec 8 graphiques Chart.js
- Recherche intelligente par titre, contenu, tags
- Compteur de partages
- Synchronisation automatique vers le serveur (fire-and-forget)
- Protection CSRF + sanitisation HTML (Bleach)

### Application SERVEUR

- 9 endpoints REST pour la synchronisation
- Dashboard global : KPIs, tendances, top articles, répartition devices/navigateurs
- Statistiques articles : total, publiés, brouillons, supprimés, par catégorie, par auteur
- Analyse détaillée par article : vues, commentaires, engagement, mots-clés, tendances 30j/7j
- Statistiques utilisateurs : actifs, inactifs, rôles, inscriptions, activité
- Détection automatique du type d'appareil (iPhone, Android, Tablette, Ordinateur)
- Détection navigateur et OS
- Graphiques doughnut, barres, lignes (Chart.js 4)

---

## Statistiques du projet

| Métrique | Valeur |
|---|---|
| Applications Django | 2 |
| Modèles de données | 19 (6 client + 12 serveur + 1 legacy) |
| Endpoints API | 9 sync + 2 legacy |
| Templates HTML | 15+ |
| Feuilles CSS | 7 |
| Catégories article | 20 prédéfinies |
| Langue | Français |
