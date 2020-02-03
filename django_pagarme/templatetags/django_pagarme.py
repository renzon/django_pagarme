from django import template
from django.conf import settings

from django_pagarme.models import Sellable

register = template.Library()


@register.inclusion_tag('django_pagarme/pagarme_js_form.html')
def show_pagarme(sellable: Sellable):
    return {
        'sellable': sellable,
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
