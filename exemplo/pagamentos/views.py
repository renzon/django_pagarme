# Create your views here.
from collections import ChainMap

from django.conf import settings
from django.shortcuts import render
from pagarme import authentication_key

from django_pagarme import facade

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


def produto(request, slug: str):
    open_modal = request.GET.get('open_modal', '').lower() == 'true'
    customer_qs_data = {k: request.GET.get(k, '') for k in ['name', 'email', 'phone']}
    customer_qs_data = {k: v for k, v in customer_qs_data.items() if v}
    user = request.user
    if user.is_authenticated:
        user_data = {'external_id': user.id, 'name': user.first_name, 'email': user.email}
        customer = ChainMap(customer_qs_data, user_data)
    else:
        customer = customer_qs_data
    ctx = {
        'payment_item': facade.get_payment_item(slug),
        'open_modal': open_modal,
        'customer': customer,
    }
    return render(request, 'pagamentos/produto.html', ctx)
