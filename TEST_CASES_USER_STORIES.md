# 📋 User Stories & Test Cases - Digital Scholar System

**Document de spécification complet avec 40+ User Stories et leurs Test Cases associés**

---

## 📑 Table des matières

1. [Authentification & Gestion des Utilisateurs](#authentification--gestion-des-utilisateurs)
2. [Gestion des Articles](#gestion-des-articles)
3. [Publication et Statuts](#publication-et-statuts)
4. [Commentaires des Lecteurs](#commentaires-des-lecteurs)
5. [Analytics et Tracking](#analytics-et-tracking)
6. [Dashboard Auteur](#dashboard-auteur)
7. [Dashboard Admin - Serveur](#dashboard-admin---serveur)
8. [API & Synchronisation](#api--synchronisation)
9. [Sécurité, Performance & Responsive](#sécurité-performance--responsive)

---

## 🔐 Authentification & Gestion des Utilisateurs

### US.1 - Inscription d'un Auteur
**Description:** Un nouvel utilisateur doit pouvoir créer un compte auteur pour accéder à la plateforme.

**Critères d'acceptation:**
- Accès à la page d'inscription `/accounts/signup/`
- Champs requis: username, prénom, nom, email, mot de passe
- Validation email unique (case-insensitive)
- Vérification correspondance mots de passe
- Redirection vers dashboard après création réussie
- Notification de succès affichée

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.1.1 | Inscription valide complète | username: juan.lopez, email: juan@edu.com, prénom: Juan, nom: Lopez, pwd: SecurePass123! | Utilisateur créé, email trouvé en BDD, redirection /dashboard/ | 🔴 Critique |
| TC.1.2 | Email déjà utilisé (case diff) | email: EXISTING@example.com (existe: existing@example.com) | Erreur "Un compte avec cet email existe déjà" | 🔴 Critique |
| TC.1.3 | Mots de passe non identiques | password1: Pass123!, password2: Pass456! | Erreur "Les mots de passe ne correspondent pas" | 🔴 Critique |
| TC.1.4 | Prénom manquant | Laisser prénom vide | Erreur "Ce champ est obligatoire" | 🟡 High |
| TC.1.5 | Username déjà existant | username: existing_user | Erreur "Ce nom d'utilisateur est déjà pris" | 🟡 High |
| TC.1.6 | Mot de passe trop court | password: "123" | Erreur "Le mot de passe doit avoir au moins 8 caractères" | 🟡 High |
| TC.1.7 | Email format invalide | email: "notanemail" | Erreur de validation email | 🟢 Medium |

---

### US.2 - Connexion d'un Auteur
**Description:** Un auteur enregistré doit pouvoir se connecter à son compte.

**Critères d'acceptation:**
- Accès au formulaire de connexion `/accounts/login/`
- Validation des identifiants (username/email + password)
- Session créée avec HTTPONLY cookie
- Redirection vers `/dashboard/` après connexion
- Message d'erreur en cas d'identifiants incorrects

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.2.1 | Connexion valide | username: juan.lopez, password: SecurePass123! | Connexion réussie, session créée, redirection dashboard | 🔴 Critique |
| TC.2.2 | Connexion avec email | email: juan@edu.com, password: SecurePass123! | Connexion réussie | 🟡 High |
| TC.2.3 | Username incorrect | username: unknown.user, password: Pass123 | Erreur "Identifiants invalides" | 🔴 Critique |
| TC.2.4 | Mot de passe incorrect | username: juan.lopez, password: WrongPass | Erreur "Identifiants invalides" | 🔴 Critique |
| TC.2.5 | Champs vides | username: "", password: "" | Erreur "Veuillez remplir tous les champs" | 🟡 High |
| TC.2.6 | Tentatives brute-force | 10 essais échoués en 1 minute | Compte verrouillé 15 minutes | 🟢 Medium |

---

### US.3 - Déconnexion d'un Auteur
**Description:** Un auteur connecté doit pouvoir se déconnecter.

**Critères d'acceptation:**
- Bouton "Déconnexion" visible pour auteurs authentifiés
- Suppression session lors du clic
- Suppression du HTTPONLY cookie
- Redirection vers `/` (home)

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.3.1 | Déconnexion réussie | Utilisateur connecté, clic "Déconnexion" | Session supprimée, redirection home | 🔴 Critique |
| TC.3.2 | Accès dashboard après logout | URL: /dashboard/ (après logout) | Redirection vers /login/ | 🔴 Critique |
| TC.3.3 | Cookie supprimé | Vérifier cookies au logout | HTTPONLY cookie absent | 🟡 High |

---

## 📝 Gestion des Articles

### US.4 - Création d'un Article
**Description:** Un auteur authentifié crée un nouvel article éducatif.

**Critères d'acceptation:**
- Accès à `/articles/new/` uniquement si authentifié
- Tous les champs requis: titre, catégorie, intro, contenu, conclusion, objectifs, questions
- Slug généré automatiquement à partir du titre (slugify)
- Article sauvegardé en statut DRAFT par défaut
- enable_analytics par défaut à True
- Redirection vers article_detail après création

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.4.1 | Création minimale | titre: "Les Pyramides", catégorie: histoire_simplifiee, intro: "...", contenu: "...", conclusion: "...", objectifs: "Apprendre l'histoire", questions: "Qu'est-ce qu'une pyramide?" | Article créé, status=DRAFT, slug="les-pyramides" | 🔴 Critique |
| TC.4.2 | Titre manquant | Laisser titre vide | Erreur "Ce champ est obligatoire" | 🔴 Critique |
| TC.4.3 | Catégorie invalide | Sélectionner catégorie inexistante | Erreur de validation | 🟡 High |
| TC.4.4 | Slug dupliqué | Deux articles titre: "Test" | 2ème article: slug="test-2" (auto-resolve) | 🟡 High |
| TC.4.5 | Upload illustration | Fichier: image.jpg (500KB) | Image stockée dans media/articles/images/, illustration_upload rempli | 🟢 Medium |
| TC.4.6 | URL illustration externe | illustration_url: "https://example.com/img.png" | URL validée et stockée | 🟢 Medium |
| TC.4.7 | Tags CSV | tags_csv: "maths, géométrie, sciences" | 3 tags créés et liés | 🟢 Medium |
| TC.4.8 | Multimédia complète | illustration, vidéo_url, audio_url, ressouces | Tous stockés | 🟢 Medium |
| TC.4.9 | Non-authentifié | Accès direct /articles/new/ | Redirection /login/ | 🔴 Critique |

---

### US.5 - Édition d'un Article
**Description:** L'auteur peut modifier son propre article.

**Critères d'acceptation:**
- Accès `/articles/<slug>/edit/` uniquement propriétaire
- Modification tous champs sauf slug (immuable)
- updated_at mis à jour automatiquement
- Brouillons et publiés tous modifiables
- Notification de modification

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.5.1 | Modification propre article | Changer titre + contenu | Article modifié, updated_at récent | 🔴 Critique |
| TC.5.2 | Modification tags | Ajouter "histoire" | Tags actualisés | 🟡 High |
| TC.5.3 | Suppression illustration | Retirer illustration_url | URL supprimée | 🟡 High |
| TC.5.4 | Autre auteur | Accéder /articles/juans-article/edit/ (autre auteur) | Erreur 403 Forbidden | 🔴 Critique |
| TC.5.5 | Non-authentifié | Accès direct /edit/ | Redirection /login/ | 🔴 Critique |
| TC.5.6 | Slug ne change pas | Modifier titre | Slug inchangé | 🟡 High |

---

### US.6 - Suppression d'un Article
**Description:** L'auteur peut supprimer son article avec confirmation.

**Critères d'acceptation:**
- Affichage modal confirmation avant suppression
- Suppression en cascade: commentaires, analytics, logs
- Seul propriétaire peut supprimer
- Redirection vers list articles après suppression

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.6.1 | Suppression confirmée | Article sans dépendances, clic Supprimer + OK | Article supprimé, redirection /articles/ | 🔴 Critique |
| TC.6.2 | Suppression annulée | Clic Supprimer + Annuler | Article conservé | 🟡 High |
| TC.6.3 | Cascade commentaires | Article avec 5 commentaires | Tous les commentaires supprimés | 🟡 High |
| TC.6.4 | Autre auteur | Tentative suppression article autre | Erreur 403 | 🔴 Critique |
| TC.6.5 | Suppression avec analytics | Article avec 100 vues | Analytics et RawEvents supprimés | 🟢 Medium |

---

### US.7 - Liste des Articles d'un Auteur
**Description:** L'auteur voit ses articles avec statistiques dans son dashboard.

**Critères d'acceptation:**
- Affichage articles propriétaire uniquement
- Stats par article: vues, commentaires, partages
- Distinction DRAFT vs PUBLISHED (UI différente)
- Filtrage par statut opérationnel
- Tri par date création (récent en premier)

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.7.1 | Liste avec articles | 5 articles propriétaire | 5 articles affichés avec stats | 🔴 Critique |
| TC.7.2 | Aucun article | Nouvel auteur | Message "Aucun article créé" | 🟡 High |
| TC.7.3 | Filtre DRAFT | Clic "Brouillons" | Articles status=DRAFT uniquement | 🟡 High |
| TC.7.4 | Filtre PUBLISHED | Clic "Publiés" | Articles status=PUBLISHED uniquement | 🟡 High |
| TC.7.5 | Stats correctes | Article avec 50 vues, 3 commentaires | Stats affichées correctement | 🟡 High |

---

## 🚀 Publication et Statuts

### US.8 - Publication d'un Article
**Description:** L'auteur publie un brouillon pour le rendre visible aux lecteurs.

**Critères d'acceptation:**
- Statut change DRAFT → PUBLISHED
- published_at défini à now()
- Article immédiatement visible en public
- Sync au serveur déclenchée
- Notification optionnelle (future)

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.8.1 | Publication article | Article DRAFT, clic "Publier" | status=PUBLISHED, published_at=now(), article visible | 🔴 Critique |
| TC.8.2 | Lecteur voit article | Visiter URL article après publication | Article affiché, commentaires/partages visibles | 🔴 Critique |
| TC.8.3 | Sync serveur | Publication article | POST /api/sync/article/ déclenché | 🟡 High |
| TC.8.4 | Analytics trackées | Lecteur visite après publication | AnalyticsEvent créés | 🟡 High |

---

### US.9 - Dépublication d'un Article
**Description:** L'auteur rend brouillon un article pub lié.

**Critères d'acceptation:**
- Statut PUBLISHED → DRAFT
- Article non accessible publiquement (404)
- Analytics conservées (historique)
- Sync au serveur

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.9.1 | Dépublication | Article PUBLISHED, clic "Archiver" | status=DRAFT | 🔴 Critique |
| TC.9.2 | Article invisible | Visiteur accède URL article archivé | 404 Not Found | 🔴 Critique |
| TC.9.3 | Analytics conservées | Article avec historique | Données gardées | 🟢 Medium |

---

## 💬 Commentaires des Lecteurs

### US.10 - Ajout de Commentaire
**Description:** Un lecteur (anonyme) commente un article publié.

**Critères d'acceptation:**
- Commentaires uniquement sur articles PUBLISHED
- Champs: name (défaut "Lecteur"), email (optionnel), message (max 1000 char)
- Commentaire approuvé par défaut (is_approved=True)
- Possibilité de répondre (parent_id)
- Sync serveur déclenché

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.10.1 | Commentaire valide | name: "Alice", message: "Excellent article!" | Commentaire créé, is_approved=True | 🔴 Critique |
| TC.10.2 | Commentaire sans nom | Laisser name vide | Défaut "Lecteur", message enregistré | 🟡 High |
| TC.10.3 | Email optionnel | Laisser email vide | Enregistré, email blank | 🟢 Medium |
| TC.10.4 | Message trop long | 1500 caractères | Erreur "Max 1000 caractères" | 🟡 High |
| TC.10.5 | Réponse commentaire | Reply à comment ID 7 | parent_id=7, imbrication créée | 🟡 High |
| TC.10.6 | Article DRAFT | Tenter réponse sur DRAFT | 404 Not Found | 🔴 Critique |
| TC.10.7 | Sync serveur | Nouveau commentaire | POST /api/sync/comment/ envoyé | 🟢 Medium |

---

### US.11 - Affichage des Commentaires
**Description:** Commentaires affichés hiérarchiquement sous l'article.

**Critères d'acceptation:**
- Seuls commentaires is_approved=True affichés
- Structure hiérarchique (réponses indentées)
- Tri chronologique (ancien → récent)
- Affichage: name, message, date, imbrication

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.11.1 | Affichage approuvés | 3 commentaires is_approved=True | 3 affichés | 🔴 Critique |
| TC.11.2 | Non-approuvés cachés | 2 comments is_approved=False | 0 affiché | 🔴 Critique |
| TC.11.3 | Hiérarchie | Comment + 2 réponses | Réponses indentées | 🟡 High |
| TC.11.4 | Tri chrono | 3 comments: créés à 10h, 11h, 12h | Affichés 10h → 12h | 🟡 High |

---

## 📊 Analytics et Tracking

### US.12 - Tracking des Vues d'Article
**Description:** Chaque accès article enregistre une lecture.

**Critères d'acceptation:**
- AnalyticsEvent créé par lecture
- Section suivie (Intersection Observer)
- Durée section en secondes
- Session ID unique par session
- Device/Browser détectés
- Sync si enable_analytics=True
- IP et User-Agent enregistrés

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.12.1 | Vue article | Accès article | AnalyticsEvent créé, section=intro | 🔴 Critique |
| TC.12.2 | Durée section | Lire 45s section content | duration_seconds=45 | 🟡 High |
| TC.12.3 | Analytics OFF | Article enable_analytics=False | Event local, pas sync | 🟡 High |
| TC.12.4 | Session ID | 2 accès même lecteur | Même session_id | 🟡 High |
| TC.12.5 | Device detection | Accès mobile | device_type="iPhone"/"Android"/"Tablette" | 🟢 Medium |
| TC.12.6 | Browser détecté | Accès Firefox | browser="Firefox" | 🟢 Medium |
| TC.12.7 | IP enregistrée | Lecture article | IP stockée | 🟢 Medium |

---

### US.13 - Tracking des Partages
**Description:** Les partages d'articles sont comptabilisés.

**Critères d'acceptation:**
- Action track_share déclenché
- Plateforme enregistrée (Facebook, Twitter, etc.)
- Compteur partagé mis à jour
- Sync serveur

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.13.1 | Partage Facebook | Clic partage Facebook | event type=share, platform=facebook | 🟡 High |
| TC.13.2 | Compteur | 5 partages | share_count=5 | 🟡 High |
| TC.13.3 | Lien copie | Copier lien article | event type=share, platform=copy_link | 🟢 Medium |

---

### US.14 - Désactivation Analytics par Article
**Description:** L'auteur peut opt-out du tracking analytique.

**Critères d'acceptation:**
- Checkbox enable_analytics dans formulaire article
- Events locaux créés mais non synced
- Affichage "Analytics désactivés" en article_detail

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.14.1 | Désactiver | enable_analytics=False | Events non-envoyés au serveur | 🟡 High |
| TC.14.2 | Réactiver | enable_analytics=False → True | Prochains events synced | 🟡 High |
| TC.14.3 | Affichage UI | Article désactivé | Badge "Analytics désactivés" visible | 🟢 Medium |

---

## 👨‍💼 Dashboard Auteur

### US.15 - Vue Dashboard Auteur
**Description:** Tableau de bord personnel avec statistiques.

**Critères d'acceptation:**
- Accès `/dashboard/` authentifiés uniquement
- KPIs: articles, vues, commentaires, partages
- Graphiques Chart.js (tendances, devices, sections)
- Stats agrégées par article
- Filtrage périodes (7j, 30j, custom)

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.15.1 | Vue dashboard | Auteur authentifié | Dashboard chargé, KPIs visibles | 🔴 Critique |
| TC.15.2 | Stats article | Article: 100 vues, 5 comments, 2 shares | Stats correctes | 🔴 Critique |
| TC.15.3 | Non-authentifié | Accès /dashboard/ | Redirection /login/ | 🔴 Critique |
| TC.15.4 | Graphique tendance | 7j données | Graphique Chart.js généré | 🟡 High |
| TC.15.5 | Filtre 7j/30j | Clic "7 derniers jours" | Données filtrées | 🟡 High |
| TC.15.6 | Breakdown sections | Article avec plusieurs sections | Temps par section affiché | 🟢 Medium |

---

### US.16 - Actions Dashboard
**Description:** Contrôles pour CRUD articles depuis dashboard.

**Critères d'acceptation:**
- Bouton "Nouvel article" → /articles/new/
- Lien article → article_detail
- Bouton "Éditer" → article_edit
- Bouton "Publier/Dépublier" → toggle status
- Bouton "Supprimer" → delete avec confirmation

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.16.1 | Créer article | Clic "Nouvel article" | Redirection /articles/new/ | 🔴 Critique |
| TC.16.2 | Voir détail | Clic article | Redirection article_detail | 🟡 High |
| TC.16.3 | Éditer | Clic "Éditer" | Redirection edit form | 🟡 High |
| TC.16.4 | Publier | Clic bouton publish | status=PUBLISHED | 🔴 Critique |
| TC.16.5 | Supprimer | Clic delete + OK | Article supprimé | 🟡 High |

---

## 🖥️ Dashboard Admin - Serveur

### US.17 - Vue Dashboard Global
**Description:** Vue d'ensemble analytique sur tous les contenus.

**Critères d'acceptation:**
- KPIs: articles publiés, auteurs, lecteurs uniques
- Top 10 articles vues
- Top 10 auteurs engagement
- Tendance globales (7j, 30j)
- Graphiques Chart.js
- Filtrage période

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.17.1 | Dashboard charges | Admin authentifié | KPIs, graphiques visibles | 🔴 Critique |
| TC.17.2 | Top articles | 100 articles | Top 10 par vues affiché | 🟡 High |
| TC.17.3 | Tendance globale | 30j données | Graphique publication/jour | 🟡 High |
| TC.17.4 | Filtre période | Clic "7 jours" vs "30 jours" | Données refiltrées | 🟢 Medium |

---

### US.18 - Explorateur d'Articles
**Description:** Interface exploration tous articles avec filtrage.

**Critères d'acceptation:**
- Liste pagées (20/page)
- Filtres: catégorie, auteur, statut
- Recherche full-text (titre, tags, contenu)
- Tri par: titre, date, vues, commentaires
- Affichage: titre, auteur, vues, comments

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.18.1 | Liste articles | Explorateur chargé | 20 articles affichés | 🔴 Critique |
| TC.18.2 | Filtre catégorie | Sélectionner "Maths ludiques" | Articles filtrés | 🟡 High |
| TC.18.3 | Recherche | Query: "pyramides" | Articles contenant word | 🟡 High |
| TC.18.4 | Tri vues | Tri ↓ vues | Vues_count descending | 🟡 High |
| TC.18.5 | Pagination | Page 2 | Articles 21-40 | 🟢 Medium |
| TC.18.6 | Filtre auteur | Auteur: "Jean Dupont" | Articles Jean | 🟢 Medium |

---

### US.19 - Détail Article (Vue Admin)
**Description:** Détail analytique complet d'un article.

**Critères d'acceptation:**
- Infos article (titre, auteur, catégorie, status)
- Métriques: total_reads, avg_time, visibility%
- Breakdown sections (temps par section)
- Graphique lectures/jour (7j)
- Commentaires (count, % approuvés)

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.19.1 | Détail article | Clic article explorateur | Métriques chargées | 🔴 Critique |
| TC.19.2 | Breakdown sections | Article > 1000 reads | Temps par section calculé | 🟡 High |
| TC.19.3 | Graphique 7j | 7j données | Chart.js générée | 🟡 High |
| TC.19.4 | Stats comments | 12 comments (10 approvés) | Count + % affichés | 🟢 Medium |

---

### US.20 - Vue Tendances
**Description:** Analyse tendances globales plateforme.

**Critères d'acceptation:**
- Top articles semaine/mois
- Top auteurs ascendants
- Catégories populaires
- Graphiques évolutifs
- Comparaison périodes

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.20.1 | Top articles | 7j données | Top 5 par vues | 🟡 High |
| TC.20.2 | Catégories pop | Toutes catégories | Répartition vues | 🟡 High |
| TC.20.3 | Comparaison | Semaine1 vs Semaine2 | % croissance affichée | 🟢 Medium |

---

### US.21 - Vue Auteurs
**Description:** Gestion et suivi des auteurs.

**Critères d'acceptation:**
- Liste tous auteurs
- Stats: articles, vues totales, commentaires, engagement
- Filtre actifs/inactifs
- Détail auteur complet

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.21.1 | Liste auteurs | Explorateur auteurs | Tous listés | 🟡 High |
| TC.21.2 | Stats auteur | 5 articles, 500 vues | Stats calculées | 🟡 High |
| TC.21.3 | Détail | Clic auteur | Articles + stats affichés | 🟡 High |

---

### US.22 - Vue Utilisateurs
**Description:** Suivi activité lecteurs/sessions.

**Critères d'acceptation:**
- Nombre sessions uniques
- Devices/navigateurs populaires
- Localisation (par IP)
- Utilisateurs réguliers vs nouveaux
- Historique actions

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.22.1 | Sessions | Tracker activé | Sessions uniques comptées | 🟡 High |
| TC.22.2 | Device breakdown | 1000 lectures | % mobile/desktop/tablette | 🟡 High |
| TC.22.3 | Navigateurs | Analytics | Firefox, Chrome, Safari % | 🟢 Medium |

---

## 🔗 API & Synchronisation

### US.23 - Synchronisation Utilisateurs
**Description:** Sync users client → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/user/`
- Champs: user_id, username, first_name, last_name, email
- Créer ou update Teacher en serveur
- Réponse 200: `{"ok": true}`

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.23.1 | Sync user nouveau | POST user_id=5, username=juan | Teacher créé client_user_id=5 | 🟡 High |
| TC.23.2 | Update existant | POST user_id=5 (existe) updated data | Teacher mis à jour | 🟡 High |
| TC.23.3 | Réponse 200 | Request valide | `{"ok": true}` | 🔴 Critique |
| TC.23.4 | Payload invalide | JSON broken | HTTP 400, `{"ok": false, "error": "..."}` | 🟡 High |

---

### US.24 - Synchronisation Articles
**Description:** Sync articles client → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/article/`
- Champs: article_id, title, author_id, category, status, published_at
- Créer/update ClientArticle + ArticleMetrics
- Réponse 200 OK

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.24.1 | Sync article nouveau | POST article_id=10 | ClientArticle créé, metrics créées | 🟡 High |
| TC.24.2 | Update article | POST article_id=10 (existe) modifié | ClientArticle updated | 🟡 High |
| TC.24.3 | Published_at set | status=PUBLISHED, published_at="2026-04-14T10:00:00Z" | published_at sauvegardé | 🟡 High |

---

### US.25 - Suppression Article
**Description:** Sync suppression article client → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/article-delete/`
- Suppression ClientArticle, metrics, daily_reads, raw_events
- Suppression en cascade
- Réponse 200 OK

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.25.1 | Suppression | POST article_id=10 | Article supprimé du serveur | 🟡 High |
| TC.25.2 | Cascade | Article avec 5k reads | Tous RawEvent supprimés | 🟡 High |

---

### US.26 - Synchronisation Commentaires
**Description:** Sync commentaires client → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/comment/`
- Champs: comment_id, article_id, name, message, created_at
- Créer/update ClientReaderComment
- Compteur article_comments

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.26.1 | Sync comment | POST comment_id=20 | ClientReaderComment créé | 🟢 Medium |
| TC.26.2 | Count agrégé | Article + 5 comments | Serveur article.comments_count=5 | 🟢 Medium |

---

### US.27 - Synchronisation Analytics Events
**Description:** Sync events lecteur → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/event/`
- Champs: article_id, section, duration_seconds, device_type, browser, session_id
- Créer RawEvent type=analytics
- Agrégation ArticleMetrics

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.27.1 | Sync event | POST section=content, duration=45 | RawEvent créé | 🟡 High |
| TC.27.2 | Agrégation | 10 events article | metrics.total_reads+=10, content_seconds+=total | 🟡 High |
| TC.27.3 | Per-section | section=intro, conclusion | Champs respectifs updated | 🟢 Medium |

---

### US.28 - Synchronisation Action Logs
**Description:** Sync logs actions client → serveur.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/action-log/`
- Actions: signup, article_view, article_share, article_create, comment_create
- Création RawEvent type=action_log
- Audit trail complet

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.28.1 | Log signup | action=author_signup | RawEvent + ActionLog créés | 🟡 High |
| TC.28.2 | Log view | action=article_view | ActionLog article_id set | 🟡 High |
| TC.28.3 | Log share | action=article_share | RawEvent enregistré | 🟢 Medium |

---

### US.29 - Synchronisation Complète
**Description:** Sync atomique tous les éléments.

**Critères d'acceptation:**
- Endpoint POST `/api/sync/full/`
- Multiple users, articles, comments, events, logs en une requête
- Transaction Django: tout ou rien
- Réponse 200 OK ou 400 error

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.29.1 | Sync complète | Full payload valide | Tous éléments créés, 200 OK | 🔴 Critique |
| TC.29.2 | Erreur partielle | 1 item invalide | Rollback, 400 error | 🟡 High |
| TC.29.3 | Performances | 1000 articles | Complète < 5s | 🟢 Medium |

---

## 🔒 Sécurité, Performance & Responsive

### US.30 - Validation & Sanitisation
**Description:** Toutes entrées validées et sécurisées.

**Critères d'acceptation:**
- HTML sanitisé avec bleach
- SQL injection prévenue (ORM Django)
- XSS prévenue (template escaping)
- Longueur max respectée
- Types validés

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.30.1 | XSS commentaire | message=`<script>alert('xss')</script>` | Script supprimé, texte d'affichage | 🔴 Critique |
| TC.30.2 | Bleach HTML | `<p>Text</p><script>` | `<p>Text</p>` (script stripped) | 🔴 Critique |
| TC.30.3 | SQL injection | username=`' OR '1'='1` | Pas exécuté, erreur validation | 🔴 Critique |

---

### US.31 - Protection CSRF
**Description:** Protection contre cross-site attaques.

**Critères d'acceptation:**
- Token CSRF obligatoire en POST
- Vérification django.middleware.csrf
- Rejet sans token valide
- Cookies HTTPONLY

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.31.1 | POST sans token | Form POST, pas de csrf token | HTTP 403 Forbidden | 🔴 Critique |
| TC.31.2 | POST avec token | Valid csrf token | Accepté 200 OK | 🔴 Critique |

---

### US.32 - Authentification Obligatoire
**Description:** Endpoints sensibles protégés.

**Critères d'acceptation:**
- Dashboard nécessite login
- Creation/edit/delete nécessitent login
- Redirection vers /login/ pour non-auth

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.32.1 | Dashboard non-auth | Accès direct /dashboard/ | Redirection /login/ | 🔴 Critique |
| TC.32.2 | Edit non-auth | Accès /articles/slug/edit/ | Redirection /login/ | 🔴 Critique |

---

### US.33 - Responsive Design
**Description:** Application fonctionnelle tous devices.

**Critères d'acceptation:**
- Mobile <480px: optimisé
- Tablet 480-1024px: layout adapté
- Desktop >1024px: complet
- Navigation mobile accessible

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.33.1 | Mobile | Viewport 375px | Texte lisible, images adaptées | 🟡 High |
| TC.33.2 | Tablet | Viewport 768px | Layout 2-colonnes adapté | 🟡 High |
| TC.33.3 | Desktop | Viewport 1920px | Layout complet | 🟢 Medium |
| TC.33.4 | Menu mobile | Hamburger menu | Déroulant, accessible | 🟡 High |

---

### US.34 - Performance & Caching
**Description:** Application rapide et optimisée.

**Critères d'acceptation:**
- Page article <2s LCP (Largest Contentful Paint)
- Dashboard <3s
- Images lazy-loaded
- Pas N+1 queries

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.34.1 | Article LCP | Load article | LCP < 2s | 🟡 High |
| TC.34.2 | Dashboard | Load dashboard | < 3s | 🟡 High |
| TC.34.3 | Lazy images | Liste articles | Images lazy-loadées | 🟢 Medium |
| TC.34.4 | Requêtes | Profiling Django | Pas N+1 | 🟡 High |

---

## 🎯 Flux Intégration (End-to-End)

### US.35 - Flux Complet Auteur
**Description:** Parcours complet: signup → article → publication → stats.

**Étapes:**
1. Signup auteur
2. Création article complet
3. Publication
4. 10 lecteurs visitent (track analytics)
5. Lecteurs commentent
6. Vérifier stats dashboard

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.35.1 | E2E complet | Suite étapes 1-6 | Stats correctes (10 vues, x commentaires) | 🔴 Critique |
| TC.35.2 | Sync serveur | Chaque étape | Serveur à jour en temps réel | 🟡 High |
| TC.35.3 | Graphiques | Dashboard auteur | Tendances tracées | 🟢 Medium |

---

### US.36 - Flux Complet Lecteur
**Description:** Parcours lecteur: découverte → lecture → engagement.

**Étapes:**
1. Visiteur accès home
2. Ouvre article
3. Lit sections (track par Intersection Observer)
4. Ajoute commentaire
5. Partage article
6. Serveur recoit et agrège tout

**Test Cases:**

| ID | Scénario | Données | Résultat attendu | Priorité |
|---|---|---|---|---|
| TC.36.1 | Reader E2E | Suite actions 1-6 | Tous events enregistrés | 🔴 Critique |
| TC.36.2 | Analytics détaillées | Lire 3 sections | Durée par section tracked | 🟡 High |
| TC.36.3 | Dashboard auteur | Après reader E2E | Stats mises à jour | 🟡 High |

---

## 📊 Résumé & Priorisation

### Statistiques
- **User Stories total:** 36
- **Test Cases total:** 200+
- **Cas critiques (🔴):** ~50
- **Cas haute priorité (🟡):** ~100
- **Cas moyenne/basse (🟢):** ~60

### Priorisation de test

**Phase 1 - Critique (Semaine 1-2):**
- US.1-6 (Auth & Articles)
- US.12-14 (Analytics)
- US.23-29 (API Sync)

**Phase 2 - High (Semaine 3):**
- US.7-11 (CRUD avancé)
- US.15-22 (Dashboards)
- US.30-32 (Sécurité)

**Phase 3 - Medium (Semaine 4+):**
- US.33-36 (Performance, responsive, E2E)

---

**Dernière mise à jour:** 14 Avril 2026  
**Statut:** Document de référence   
**Audience:** QA Engineers, Développeurs, Product Managers
