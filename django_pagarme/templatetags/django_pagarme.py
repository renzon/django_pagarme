from django import template
from django.conf import settings
from django.urls import reverse

from django_pagarme.models import PagarmeItemConfig, Plan

register = template.Library()


@register.inclusion_tag('django_pagarme/pagarme_js_form.html')
def show_pagarme(payment_item: PagarmeItemConfig = None, customer: dict = None, address=None, open_modal: bool = False,
                 review_informations: bool = True, plan: Plan = None):
    if payment_item is not None:
        kwargs = {'slug': payment_item.slug}
    elif plan is not None:
        kwargs = {'slug': plan.slug}
    notification_path = reverse('django_pagarme:notification', kwargs=kwargs)
    domain = settings.ALLOWED_HOSTS[0]
    return {
        'payment_item': payment_item,
        'plan': plan,
        'open_modal': open_modal,
        'review_informations': review_informations,
        'customer': customer,
        'address': address,
        'postback_url': f'https://{domain}{notification_path}',
        'CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA': settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA
    }


def interest_rate(value):
    try:
        value = float(value)
    except ValueError:
        return ''
    else:
        return f'{value:.2f}'


def cents_to_brl(value):
    try:
        value = int(value)
    except ValueError:
        return ''
    else:
        value /= 100  # to brl
        return f'R$ {value:,.2f}'.replace('.', '@').replace(',', '.').replace('@', ',')


register.filter('interest_rate', interest_rate)
register.filter('cents_to_brl', cents_to_brl)
