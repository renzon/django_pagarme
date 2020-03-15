from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render
from pagarme import authentication_key

from django_pagarme import facade

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


def user_factory(pagarme_transaction):
    User = get_user_model()
    customer = pagarme_transaction['customer']
    try:
        return User.objects.get(email=customer['email'])
    except User.DoesNotExist:
        return User.objects.create(
            first_name=customer['name'],
            email=customer['email']
        )


def print_contact_info(*args, **kwargs):
    print('Contact Data:', args, kwargs)


facade.set_user_factory(user_factory)
facade.add_contact_info_listener(print_contact_info)


def home(request):
    ctx = {'payment_items': facade.list_payment_item_configs()}
    return render(request, 'home.html', ctx)
