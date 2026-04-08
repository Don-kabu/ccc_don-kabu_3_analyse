"""
seed_test_data – Génère un jeu de données de test réaliste dans les
modèles Client* du serveur analytique (sans passer par l'API sync).

Usage :
    python manage.py seed_test_data
    python manage.py seed_test_data --flush   # supprime puis recrée
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.models import (
    ClientActionLog,
    ClientAnalyticsEvent,
    ClientArticle,
    ClientArticleAnalytics,
    ClientReaderComment,
    ClientTag,
    ClientUser,
)

# ────────────────────────────── Données brutes ────────────────────────────

USERS = [
    {'username': 'amina_diallo', 'first_name': 'Amina', 'last_name': 'Diallo', 'email': 'amina@edutrack.local'},
    {'username': 'leo_martin', 'first_name': 'Léo', 'last_name': 'Martin', 'email': 'leo@edutrack.local'},
    {'username': 'sofia_benali', 'first_name': 'Sofia', 'last_name': 'Benali', 'email': 'sofia@edutrack.local'},
    {'username': 'jules_dupont', 'first_name': 'Jules', 'last_name': 'Dupont', 'email': 'jules@edutrack.local'},
    {'username': 'mariama_sow', 'first_name': 'Mariama', 'last_name': 'Sow', 'email': 'mariama@edutrack.local'},
]

TAGS = [
    ('sciences', 'sciences'), ('nature', 'nature'), ('maths', 'maths'),
    ('lecture', 'lecture'), ('emotions', 'emotions'), ('creativite', 'creativite'),
    ('histoire', 'histoire'), ('ecologie', 'ecologie'), ('musique', 'musique'),
    ('animaux', 'animaux'), ('jeux', 'jeux'), ('decouverte', 'decouverte'),
]

CATEGORIES = [
    'sciences_amusantes', 'maths_ludiques', 'histoires_contes',
    'decouverte_monde', 'activites_creatives', 'animaux_nature',
    'emotions_bienetre', 'ecologie_environnement', 'jeux_educatifs',
    'apprentissage_mots',
]

ARTICLES = [
    {
        'title': 'Pourquoi le ciel change de couleur au coucher du soleil',
        'category': 'sciences_amusantes',
        'intro': 'Quand le soleil descend, la lumière traverse plus d\'air et les couleurs se transforment.',
        'objectives': 'Comprendre la diffusion de la lumière\nObserver les couleurs du ciel',
        'content': 'La lumière blanche contient plusieurs couleurs. Dans l\'atmosphère, les particules diffusent le bleu. Au coucher du soleil, les tons orange et rouge deviennent visibles.',
        'conclusion': 'Le coucher du soleil est un excellent laboratoire naturel.',
        'reflection_questions': 'Pourquoi voit-on moins de bleu le soir ?',
        'resources': 'Observer le ciel avec un adulte',
        'tag_slugs': ['sciences', 'nature'],
    },
    {
        'title': 'Compter avec des fruits pour apprendre les additions',
        'category': 'maths_ludiques',
        'intro': 'Les mathématiques deviennent plus simples quand on manipule de vrais objets.',
        'objectives': 'Additionner jusqu\'à 20\nReprésenter une quantité',
        'content': 'Prends 3 bananes et 2 pommes. Compte chaque groupe puis rassemble-les. Exemple : 3 + 2 = 5.',
        'conclusion': 'Les additions sont plus faciles quand on voit les quantités.',
        'reflection_questions': 'Comment vérifier que 4 + 3 = 7 ?',
        'resources': 'Cartes de fruits à découper',
        'tag_slugs': ['maths', 'jeux'],
    },
    {
        'title': 'Lire une histoire et reconnaître les émotions du personnage',
        'category': 'emotions_bienetre',
        'intro': 'Les histoires aident les enfants à reconnaître les émotions.',
        'objectives': 'Identifier joie, peur, colère et tristesse\nExprimer son ressenti',
        'content': 'Lis un passage puis demande-toi ce que ressent le personnage. Cherche les indices dans les mots et les actions.',
        'conclusion': 'Comprendre les émotions dans une histoire aide à comprendre les autres.',
        'reflection_questions': 'Quel indice montre que le personnage est inquiet ?',
        'resources': 'Liste d\'émotions à illustrer',
        'tag_slugs': ['lecture', 'emotions'],
    },
    {
        'title': 'Les volcans : quand la Terre crache du feu',
        'category': 'decouverte_monde',
        'intro': 'Sous nos pieds, la Terre est brûlante. Parfois, cette chaleur remonte en surface.',
        'objectives': 'Savoir ce qu\'est un volcan\nConnaître les types d\'éruptions',
        'content': 'Un volcan est une ouverture dans la croûte terrestre. La lave sort à plus de 1000 degrés. Il existe des volcans sous-marins.',
        'conclusion': 'Les volcans façonnent notre planète depuis des milliards d\'années.',
        'reflection_questions': 'Pourquoi certains volcans sont-ils plus dangereux ?',
        'resources': 'Vidéo éruption volcanique – National Geographic Kids',
        'tag_slugs': ['sciences', 'decouverte', 'nature'],
    },
    {
        'title': 'Fabriquer un instrument de musique avec du recyclage',
        'category': 'activites_creatives',
        'intro': 'Pas besoin d\'acheter un instrument : tu peux en créer un avec ce que tu trouves chez toi.',
        'objectives': 'Créer un maracas avec une bouteille\nDécouvrir le rythme',
        'content': 'Remplis une petite bouteille avec du riz ou des lentilles. Ferme bien le bouchon. Secoue en rythme !',
        'conclusion': 'La musique est partout, même dans une bouteille de riz.',
        'reflection_questions': 'Quel autre instrument pourrais-tu fabriquer ?',
        'resources': 'Tuto vidéo DIY instruments',
        'tag_slugs': ['creativite', 'musique'],
    },
    {
        'title': 'Les abeilles : pourquoi sont-elles si importantes ?',
        'category': 'animaux_nature',
        'intro': 'Sans les abeilles, plus de fruits ni de fleurs. Découvre leur rôle extraordinaire.',
        'objectives': 'Comprendre la pollinisation\nConnaître la vie de la ruche',
        'content': 'Les abeilles transportent le pollen de fleur en fleur. Une ruche peut contenir 60 000 abeilles. La reine pond 2000 œufs par jour.',
        'conclusion': 'Protéger les abeilles, c\'est protéger notre alimentation.',
        'reflection_questions': 'Que se passerait-il sans pollinisation ?',
        'resources': 'Documentaire « La vie secrète des abeilles »',
        'tag_slugs': ['animaux', 'nature', 'ecologie'],
    },
    {
        'title': 'L\'eau : un trésor à protéger',
        'category': 'ecologie_environnement',
        'intro': 'L\'eau douce ne représente que 3% de l\'eau sur Terre. Apprenons à la préserver.',
        'objectives': 'Connaître le cycle de l\'eau\nAdopter des gestes éco-responsables',
        'content': 'L\'eau s\'évapore, forme des nuages, retombe en pluie. À la maison, fermer le robinet pendant le brossage des dents économise 12 litres.',
        'conclusion': 'Chaque goutte compte. Les petits gestes font les grandes rivières.',
        'reflection_questions': 'Combien de litres utilises-tu par jour ?',
        'resources': 'Quiz interactif « Mon empreinte eau »',
        'tag_slugs': ['ecologie', 'decouverte'],
    },
    {
        'title': 'Jouer au détective des mots : enrichir son vocabulaire',
        'category': 'apprentissage_mots',
        'intro': 'Plus tu connais de mots, mieux tu comprends le monde qui t\'entoure.',
        'objectives': 'Apprendre 5 nouveaux mots par semaine\nUtiliser le contexte pour deviner le sens',
        'content': 'Quand tu rencontres un mot inconnu, regarde les mots autour. Exemple : « Le félin se faufile silencieusement ». Félin = un animal qui se déplace doucement, comme un chat.',
        'conclusion': 'Chaque nouveau mot est une clé qui ouvre une porte.',
        'reflection_questions': 'Quel est le dernier mot nouveau que tu as appris ?',
        'resources': 'Carnet de vocabulaire à imprimer',
        'tag_slugs': ['lecture'],
    },
    {
        'title': 'Les dinosaures : les géants disparus',
        'category': 'histoires_contes',
        'intro': 'Il y a 66 millions d\'années, des créatures gigantesques régnaient sur la Terre.',
        'objectives': 'Connaître les principaux dinosaures\nComprendre leur disparition',
        'content': 'Le T-Rex mesurait 12 mètres. Le Brachiosaure pesait 80 tonnes. Un astéroïde de 10 km a provoqué leur extinction il y a 66 millions d\'années.',
        'conclusion': 'Les dinosaures ont disparu mais leurs descendants, les oiseaux, sont toujours parmi nous.',
        'reflection_questions': 'Si les dinosaures existaient encore, à quoi ressemblerait le monde ?',
        'resources': 'Musée d\'histoire naturelle – visite virtuelle',
        'tag_slugs': ['histoire', 'animaux', 'decouverte'],
    },
    {
        'title': 'Construire un jeu de société en famille',
        'category': 'jeux_educatifs',
        'intro': 'Inventer un jeu de société, c\'est apprendre en s\'amusant deux fois : en le créant et en y jouant.',
        'objectives': 'Définir des règles simples\nCréer un plateau de jeu\nTester et améliorer',
        'content': 'Étape 1 : Choisis un thème (animaux, espace, cuisine). Étape 2 : Dessine un parcours avec cases spéciales. Étape 3 : Écris 20 questions. Étape 4 : Joue et ajuste les règles.',
        'conclusion': 'Le meilleur jeu, c\'est celui que tu crées toi-même.',
        'reflection_questions': 'Quelle règle ajouterais-tu pour rendre le jeu plus drôle ?',
        'resources': 'Gabarit plateau de jeu à imprimer',
        'tag_slugs': ['jeux', 'creativite'],
    },
]

COMMENT_NAMES = ['Nina', 'Yanis', 'Emma', 'Lina', 'Noah', 'Jade', 'Adam', 'Léa', 'Raphaël', 'Chloé']
COMMENT_MESSAGES = [
    'Super article, j\'ai appris plein de choses !',
    'J\'ai essayé avec ma sœur et ça marche très bien.',
    'Est-ce qu\'on pourrait avoir une suite ?',
    'Merci pour les explications, c\'est très clair.',
    'J\'adore ce sujet, continuez !',
    'Ma mère a adoré lire ça avec moi.',
    'C\'est exactement ce qu\'on étudie à l\'école.',
    'J\'ai une question : pourquoi ça fonctionne comme ça ?',
    'Trop bien ! Je l\'ai partagé avec mes amis.',
    'J\'aimerais un article sur les étoiles aussi.',
    'Les images sont magnifiques.',
    'Je vais faire l\'activité ce week-end !',
    'Mon frère a trouvé ça passionnant.',
    'Bravo pour la qualité du contenu.',
    'On peut en savoir plus sur ce thème ?',
]

ACTIONS = [
    'article_view', 'article_view', 'article_view', 'article_view',  # weighted
    'article_share', 'home_view', 'article_search', 'author_dashboard_view',
    'reader_comment_created', 'analytics_tracked',
]

SECTIONS = ['introduction', 'objectifs', 'contenu', 'conclusion', 'ressources', 'article']

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

IPS = ['192.168.1.{}'.format(i) for i in range(10, 60)]


class Command(BaseCommand):
    help = 'Génère un jeu de données de test réaliste dans les modèles Client* du serveur.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Supprime les données existantes avant de recréer')

    def handle(self, *args, **options):
        now = timezone.now()

        if options['flush']:
            self.stdout.write('Suppression des données existantes…')
            ClientActionLog.objects.all().delete()
            ClientAnalyticsEvent.objects.all().delete()
            ClientArticleAnalytics.objects.all().delete()
            ClientReaderComment.objects.all().delete()
            ClientArticle.objects.all().delete()
            ClientTag.objects.all().delete()
            ClientUser.objects.all().delete()

        # ── Users ──
        users = []
        for i, u in enumerate(USERS, start=1):
            obj, created = ClientUser.objects.update_or_create(
                client_id=i,
                defaults={
                    'username': u['username'],
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                    'email': u['email'],
                    'date_joined': now - timedelta(days=random.randint(30, 365)),
                },
            )
            users.append(obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Utilisateur créé : {obj.display_name}'))

        # ── Tags ──
        tags_map = {}
        for i, (name, slug) in enumerate(TAGS, start=1):
            obj, _ = ClientTag.objects.update_or_create(
                client_id=i,
                defaults={'name': name, 'slug': slug},
            )
            tags_map[slug] = obj
        self.stdout.write(self.style.SUCCESS(f'  {len(tags_map)} tags créés'))

        # ── Articles ──
        articles = []
        for i, a_data in enumerate(ARTICLES, start=1):
            author = users[i % len(users)]
            published_at = now - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23))
            obj, _ = ClientArticle.objects.update_or_create(
                client_id=i,
                defaults={
                    'author': author,
                    'title': a_data['title'],
                    'slug': a_data['title'].lower().replace(' ', '-').replace('\'', '').replace(':', '')[:200],
                    'category': a_data['category'],
                    'intro': a_data['intro'],
                    'objectives': a_data['objectives'],
                    'content': a_data['content'],
                    'conclusion': a_data['conclusion'],
                    'reflection_questions': a_data['reflection_questions'],
                    'resources': a_data['resources'],
                    'enable_analytics': True,
                    'status': 'published',
                    'published_at': published_at,
                    'created_at': published_at - timedelta(days=random.randint(1, 7)),
                    'updated_at': published_at + timedelta(hours=random.randint(0, 48)),
                },
            )
            tag_objs = [tags_map[s] for s in a_data['tag_slugs'] if s in tags_map]
            obj.tags.set(tag_objs)
            articles.append(obj)
        self.stdout.write(self.style.SUCCESS(f'  {len(articles)} articles créés'))

        # ── Comments (3-8 per article) ──
        comment_id = 1
        total_comments = 0
        for article in articles:
            n_comments = random.randint(3, 8)
            for _ in range(n_comments):
                ClientReaderComment.objects.update_or_create(
                    client_id=comment_id,
                    defaults={
                        'article': article,
                        'name': random.choice(COMMENT_NAMES),
                        'email': '',
                        'message': random.choice(COMMENT_MESSAGES),
                        'is_approved': random.random() > 0.1,
                        'created_at': article.published_at + timedelta(
                            hours=random.randint(1, 720)),
                    },
                )
                comment_id += 1
                total_comments += 1
        self.stdout.write(self.style.SUCCESS(f'  {total_comments} commentaires créés'))

        # ── Article Analytics (1 per article) ──
        for i, article in enumerate(articles, start=1):
            reads = random.randint(20, 500)
            total_secs = reads * random.randint(30, 120)
            ClientArticleAnalytics.objects.update_or_create(
                client_id=i,
                defaults={
                    'article': article,
                    'total_reads': reads,
                    'total_seconds_read': total_secs,
                    'intro_seconds': random.randint(100, 800),
                    'objectives_seconds': random.randint(80, 600),
                    'content_seconds': random.randint(500, 3000),
                    'conclusion_seconds': random.randint(100, 700),
                    'resources_seconds': random.randint(50, 500),
                },
            )
        self.stdout.write(self.style.SUCCESS(f'  {len(articles)} analytics créés'))

        # ── Analytics Events (10-40 per article) ──
        event_id = 1
        total_events = 0
        for article in articles:
            n_events = random.randint(10, 40)
            for _ in range(n_events):
                ClientAnalyticsEvent.objects.update_or_create(
                    client_id=event_id,
                    defaults={
                        'article': article,
                        'section': random.choice(SECTIONS),
                        'duration_seconds': random.randint(5, 180),
                        'session_id': f'sess_{random.randint(1000, 9999)}',
                        'created_at': article.published_at + timedelta(
                            hours=random.randint(1, 1440)),
                    },
                )
                event_id += 1
                total_events += 1
        self.stdout.write(self.style.SUCCESS(f'  {total_events} événements analytics créés'))

        # ── Action Logs (50-150 per article, spread over time) ──
        log_id = 1
        total_logs = 0
        for article in articles:
            n_logs = random.randint(50, 150)
            for _ in range(n_logs):
                action = random.choice(ACTIONS)
                user = random.choice(users) if random.random() > 0.3 else None
                actor_type = 'author' if user else random.choice(['reader', 'anonymous'])
                created_at = article.published_at + timedelta(
                    hours=random.randint(0, 2160))  # up to 90 days after
                ua = random.choice(USER_AGENTS)
                ip = random.choice(IPS)

                ClientActionLog.objects.update_or_create(
                    client_id=log_id,
                    defaults={
                        'action': action,
                        'actor_type': actor_type,
                        'user': user,
                        'article': article,
                        'request_path': f'/articles/{article.slug}/',
                        'request_method': 'GET' if action != 'reader_comment_created' else 'POST',
                        'ip_address': ip,
                        'user_agent': ua,
                        'session_id': f'sess_{random.randint(1000, 9999)}',
                        'payload': {'action': action},
                        'created_at': created_at,
                    },
                )
                log_id += 1
                total_logs += 1
        self.stdout.write(self.style.SUCCESS(f'  {total_logs} action logs créés'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seed terminé : {len(users)} utilisateurs, {len(articles)} articles, '
            f'{total_comments} commentaires, {total_events} événements, {total_logs} logs.'
        ))
