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


def test_status_code(client, payment_item):
    resp = client.get(reverse('home'))
    assert resp.status_code == 200
