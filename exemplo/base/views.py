from django.contrib.auth import get_user_model
from django.shortcuts import render

from django_pagarme import facade


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


facade.set_user_factory(user_factory)


def print_contact_info(name, email, phone, payment_item_slug, user=None):
    print('Contact Data:', name, email, phone, payment_item_slug, user)


facade.add_contact_info_listener(print_contact_info)


def print_payment_id(payment_id):
    payment = facade.find_payment(payment_id)
    print(payment, payment.status())


facade.add_payment_status_changed(print_payment_id)


def debug_qs_strategy(pagarme_item_config, request):
    return pagarme_item_config.is_available() or request.GET.get('debug', False)


facade.set_available_payment_config_item_strategy(debug_qs_strategy)


def home(request):
    ctx = {'payment_items': facade.list_payment_item_configs(), 'plans': facade.list_plans()}
    return render(request, 'home.html', ctx)
