"""
Management command to push all client data to the analytics server.

Usage:
    python manage.py full_sync
"""
from django.core.management.base import BaseCommand
from blog.sync import full_sync


class Command(BaseCommand):
    help = 'Push all local data (users, articles, comments, analytics, events, action logs) to the analytics server.'

    def handle(self, *args, **options):
        self.stdout.write('Starting full sync to server…')
        full_sync()
        self.stdout.write(self.style.SUCCESS('Full sync complete.'))
