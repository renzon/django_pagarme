# Create your views here.
from django.conf import settings
from django.shortcuts import render
from pagarme import authentication_key

from django_pagarme import facade

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


def produto(request, slug: str):
    ctx = {'payment_item': facade.get_payment_item(slug)}
    return render(request, 'pagamentos/produto.html', ctx)
