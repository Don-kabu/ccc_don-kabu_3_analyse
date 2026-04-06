from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Article, ArticleAnalytics, ReaderComment, Tag


DEMO_USERS = [
    {
        'username': 'auteur_demo',
        'email': 'auteur.demo@edutrack.local',
        'first_name': 'Amina',
        'last_name': 'Diallo',
    },
    {
        'username': 'auteur_sciences',
        'email': 'sciences@edutrack.local',
        'first_name': 'Leo',
        'last_name': 'Martin',
    },
]


DEMO_ARTICLES = [
    {
        'title': 'Pourquoi le ciel change de couleur au coucher du soleil',
        'illustration_url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80',
        'intro': 'Quand le soleil descend, la lumiere traverse plus d air. Les couleurs ne voyagent pas toutes de la meme facon et le ciel se transforme.',
        'objectives': 'Comprendre la diffusion de la lumiere\nObserver les couleurs du ciel\nRelier science et observation du quotidien',
        'content': 'Section 1 : La lumiere blanche contient plusieurs couleurs.\n\nSection 2 : Dans l atmosphere, les petites particules diffusent surtout le bleu.\n\nSection 3 : Au coucher du soleil, la lumiere parcourt une plus grande distance et les tons orange et rouge deviennent plus visibles.\n\nActivite : Observe le ciel a differents moments et note les couleurs que tu vois.',
        'conclusion': 'Le coucher du soleil est un excellent laboratoire naturel pour comprendre la lumiere.',
        'reflection_questions': 'Pourquoi voit-on moins de bleu au coucher du soleil ?\nQuelles couleurs remarques-tu en premier ?',
        'resources': 'Observer le ciel avec un adulte\nFaire un dessin des couleurs du soir\nComparer avec des photos prises a differents moments',
        'tags': ['sciences', 'nature', 'observation'],
        'comments': [
            ('Nina', 'J ai teste hier et j ai vu du rose et du orange.'),
            ('Yanis', 'Est-ce que la pluie change aussi les couleurs du ciel ?'),
        ],
        'reads': 128,
        'seconds': 1450,
        'sections': {'intro_seconds': 180, 'objectives_seconds': 120, 'content_seconds': 720, 'conclusion_seconds': 210, 'resources_seconds': 220},
    },
    {
        'title': 'Compter avec des fruits pour apprendre les additions',
        'illustration_url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=1200&q=80',
        'intro': 'Les mathematiques deviennent plus simples quand on manipule de vrais objets.',
        'objectives': 'Additionner jusqu a 20\nRepresenter une quantite avec des objets\nVerifier une reponse en recomptant',
        'content': 'Prends 3 bananes et 2 pommes en image ou en objets. Compte chaque groupe puis rassemble-les.\n\nExemple : 3 + 2 = 5.\n\nJeu : invente trois additions avec des fruits differents.',
        'conclusion': 'Les additions sont plus faciles quand on voit et touche les quantites.',
        'reflection_questions': 'Comment verifier que 4 + 3 = 7 ?\nPeux-tu inventer une addition avec 10 objets ?',
        'resources': 'Cartes de fruits a decouper\nMini exercice a faire en famille',
        'tags': ['maths', 'activites', 'debutant'],
        'comments': [
            ('Emma', 'Je l ai fait avec des bouchons et ca marchait bien.'),
        ],
        'reads': 96,
        'seconds': 1090,
        'sections': {'intro_seconds': 120, 'objectives_seconds': 95, 'content_seconds': 610, 'conclusion_seconds': 140, 'resources_seconds': 125},
    },
    {
        'title': 'Lire une histoire et reconnaitre les emotions du personnage',
        'illustration_url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=1200&q=80',
        'intro': 'Les histoires aident les enfants a reconnaitre les emotions et a mieux parler de ce qu ils ressentent.',
        'objectives': 'Identifier joie, peur, colere et tristesse\nTrouver des indices dans un texte\nExprimer son ressenti avec des mots simples',
        'content': 'Lis un petit passage puis demande-toi ce que ressent le personnage. Cherche les indices dans les mots, les actions et les reactions.\n\nActivite : dessine le visage du personnage a trois moments differents de l histoire.',
        'conclusion': 'Comprendre les emotions dans une histoire aide aussi a mieux comprendre les autres.',
        'reflection_questions': 'Quel indice montre que le personnage est inquiet ?\nAs-tu deja ressenti la meme emotion ?',
        'resources': 'Liste d emotions a illustrer\nLecture en famille\nCarte mentale des emotions',
        'tags': ['lecture', 'emotions', 'francais'],
        'comments': [
            ('Lina', 'J aime bien chercher les indices dans les phrases.'),
        ],
        'reads': 74,
        'seconds': 860,
        'sections': {'intro_seconds': 110, 'objectives_seconds': 90, 'content_seconds': 470, 'conclusion_seconds': 95, 'resources_seconds': 95},
    },
]


class Command(BaseCommand):
    help = 'Cree des comptes auteurs et des articles de demonstration pour EduTrack.'

    def handle(self, *args, **options):
        authors = []
        for user_data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                },
            )
            if created:
                user.set_password('DemoPass123!')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Auteur cree: {user.username} / DemoPass123!"))
            authors.append(user)

        for index, article_data in enumerate(DEMO_ARTICLES):
            author = authors[index % len(authors)]
            article, created = Article.objects.get_or_create(
                title=article_data['title'],
                defaults={
                    'author': author,
                    'illustration_url': article_data['illustration_url'],
                    'intro': article_data['intro'],
                    'objectives': article_data['objectives'],
                    'content': article_data['content'],
                    'conclusion': article_data['conclusion'],
                    'reflection_questions': article_data['reflection_questions'],
                    'resources': article_data['resources'],
                    'status': Article.Status.PUBLISHED,
                    'published_at': timezone.now(),
                },
            )

            if not created:
                article.author = author
                article.illustration_url = article_data['illustration_url']
                article.intro = article_data['intro']
                article.objectives = article_data['objectives']
                article.content = article_data['content']
                article.conclusion = article_data['conclusion']
                article.reflection_questions = article_data['reflection_questions']
                article.resources = article_data['resources']
                article.status = Article.Status.PUBLISHED
                article.published_at = article.published_at or timezone.now()
                article.save()

            tags = [Tag.objects.get_or_create(name=name)[0] for name in article_data['tags']]
            article.tags.set(tags)

            ReaderComment.objects.filter(article=article).delete()
            for name, message in article_data['comments']:
                ReaderComment.objects.create(article=article, name=name, message=message, is_approved=True)

            analytics, _ = ArticleAnalytics.objects.get_or_create(article=article)
            analytics.total_reads = article_data['reads']
            analytics.total_seconds_read = article_data['seconds']
            for field_name, value in article_data['sections'].items():
                setattr(analytics, field_name, value)
            analytics.save()

            self.stdout.write(self.style.SUCCESS(f"Article pret: {article.title}"))

        self.stdout.write(self.style.SUCCESS('Jeu de donnees de demonstration charge.'))