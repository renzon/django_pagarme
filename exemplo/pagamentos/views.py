# Create your views here.
from django.conf import settings
from django.shortcuts import render
from pagarme import authentication_key

from django_pagarme import facade

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


def produto(request, slug: str):
    open_modal = request.GET.get('open_modal', '').lower() == 'true'
    customer_data = {k: request.GET.get(k, '') for k in ['name', 'email', 'phone']}
    ctx = {
        'payment_item': facade.get_payment_item(slug),
        'open_modal': open_modal,
        'customer': customer_data,
    }
    return render(request, 'pagamentos/produto.html', ctx)
