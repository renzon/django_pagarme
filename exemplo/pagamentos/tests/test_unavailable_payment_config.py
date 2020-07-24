from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from django_assertions import assert_redirects
from django_pagarme import facade
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
        available_until=before_now
    )


@pytest.fixture(params=['django_pagarme:contact_info', 'django_pagarme:pagarme'])
def resp_unavailable(client, unavailable_payment_item_config, request):
    return client.get(reverse(request.param, kwargs={'slug': unavailable_payment_item_config.slug}))


def test_unavailable_redirect(resp_unavailable, unavailable_payment_item_config):
    assert_redirects(
        resp_unavailable,
        reverse('django_pagarme:unavailable', kwargs={'slug': unavailable_payment_item_config.slug})
    )


@pytest.fixture
def available_payment_item_config(payment_config):
    return baker.make(
        PagarmeItemConfig,
        tangible=False,
        default_config=payment_config,
        available_until=None
    )


@pytest.fixture
def unavailable_strategy_mock(mocker):
    original_strategy = facade.is_payment_config_item_available
    strategy_mock = mocker.Mock(return_value=False)
    facade.set_available_payment_config_item_strategy(strategy_mock)
    yield strategy_mock
    facade.is_payment_config_item_available = original_strategy


@pytest.fixture(params=['django_pagarme:contact_info', 'django_pagarme:pagarme'])
def resp_available_item_with_unavailable_strategy(client, available_payment_item_config, request,
                                                  unavailable_strategy_mock):
    return client.get(reverse(request.param, kwargs={'slug': available_payment_item_config.slug}))


def test_available_item_with_unavailable_strategy_redirect(resp_available_item_with_unavailable_strategy,
                                                           available_payment_item_config):
    assert_redirects(
        resp_available_item_with_unavailable_strategy,
        reverse('django_pagarme:unavailable', kwargs={'slug': available_payment_item_config.slug})
    )


def test_strategy_called(resp_available_item_with_unavailable_strategy,
                         available_payment_item_config, unavailable_strategy_mock, client):
    unavailable_strategy_mock.assert_called_once_with(
        available_payment_item_config,
        resp_available_item_with_unavailable_strategy.wsgi_request
    )
