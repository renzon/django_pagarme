from django import template
from django.conf import settings
from django.urls import reverse

from django_pagarme.models import PagarmeItemConfig

register = template.Library()


@register.inclusion_tag('django_pagarme/pagarme_js_form.html')
def show_pagarme(payment_item: PagarmeItemConfig, customer: dict = None, open_modal: bool = False):
    notification_path = reverse('django_pagarme:notification')
    domain = '88c83328.ngrok.io' # TODO remove
    return {
        'payment_item': payment_item,
        'open_modal': open_modal,
        'customer': customer,
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


register.filter('interest_rate', interest_rate)
