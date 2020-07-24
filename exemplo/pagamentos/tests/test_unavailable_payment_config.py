from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from django_assertions import assert_redirects
from django_pagarme.models import PagarmeItemConfig, PagarmeFormConfig


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
def unavailable_payment_item_config(payment_config):
    before_now = timezone.now() - timedelta(seconds=1)
    return baker.make(
        PagarmeItemConfig,
        tangible=False,
        default_config=payment_config,
        deleted_at=before_now
    )


@pytest.fixture(params=['django_pagarme:contact_info', 'django_pagarme:pagarme'])
def resp_unavailable(client, unavailable_payment_item_config, request):
    return client.get(reverse(request.param, kwargs={'slug': unavailable_payment_item_config.slug}))


def test_unavailable_redirect(resp_unavailable, unavailable_payment_item_config):
    assert_redirects(
        resp_unavailable,
        reverse('django_pagarme:unavailable', kwargs={'slug': unavailable_payment_item_config.slug})
    )
