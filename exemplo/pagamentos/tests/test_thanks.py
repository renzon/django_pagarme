import pytest
from django.urls import reverse
from model_bakery import baker

from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig


@pytest.fixture
def payment_config(db):
    return baker.make(
        PagarmeFormConfig,
        max_installments=12,
        free_installment=1,
        interest_rate=1.66,
        payments_methods='boleto'
    )


@pytest.fixture
def payment_item(payment_config):
    return baker.make(
        PagarmeItemConfig,
        tangible=False,
        default_config=payment_config
    )


@pytest.fixture
def resp(client, payment_item):
    return client.get(reverse('django_pagarme:thanks', kwargs={'slug': payment_item.slug}))


def test_status_code(resp):
    assert resp.status_code == 200


def test_payment_item_availble_on_context(resp, payment_item):
    context_payment_item = resp.context['payment_item_config']
    assert payment_item == context_payment_item
