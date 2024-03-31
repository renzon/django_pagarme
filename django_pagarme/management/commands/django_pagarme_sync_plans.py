from django.core.management.base import BaseCommand

from django_pagarme.facade import synchronize_plans


class Command(BaseCommand):
    help = 'Sincroniza planos cadastrados no Pagar.me'

    def handle(self, *args, **options):
        synchronize_plans()
