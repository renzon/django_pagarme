import pytest
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains
from django_pagarme.models import PagarmeItemConfig, PagarmeFormConfig


@pytest.fixture
def payment_config(db):
    return baker.make(PagarmeFormConfig)


@pytest.fixture
def payment_item(payment_config):
    return baker.make(PagarmeItemConfig, default_config=payment_config)


@pytest.fixture
def resp(client, payment_item):
    return client.get(reverse('pagamentos:produto', kwargs={'slug': payment_item.slug}))


def test_status_code(payment_item: PagarmeItemConfig, resp):
    assert resp.status_code == 200


def test_pagarme_javascript(resp):
    assert_contains(resp, 'script src="//assets.pagar.me/checkout/1.1.0/checkout.js"')


def test_encription_key_is_present(settings, resp):
    assert_contains(resp, settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA)


def test_price(resp, payment_item: PagarmeItemConfig):
    assert_contains(resp, f"amount: {payment_item.price}")


def test_unit_price(resp, payment_item: PagarmeItemConfig):
    assert_contains(resp, f"unit_price: {payment_item.price}")


def test_max_installments(resp, payment_config: PagarmeFormConfig):
    assert_contains(resp, f'maxInstallments: {payment_config.max_installments}')


def test_default_installment(resp, payment_config: PagarmeFormConfig):
    assert_contains(resp, f'defaultInstallment: {payment_config.default_installment}')


def test_free_installment(resp, payment_config: PagarmeFormConfig):
    assert_contains(resp, f'freeInstallments: {payment_config.free_installment}')


def test_interest_rate(resp, payment_config: PagarmeFormConfig):
    assert_contains(resp, f'interestRate: {payment_config.interest_rate:.2f}')


def test_slug(resp, payment_item: PagarmeItemConfig):
    assert_contains(resp, f"id: '{payment_item.slug}'")


def test_name(resp, payment_item: PagarmeItemConfig):
    assert_contains(resp, f"title: '{payment_item.name}'")


def test_tangible(resp, payment_item: PagarmeItemConfig):
    assert_contains(resp, f"tangible: '{str(payment_item.tangible).lower()}'")


def test_payment_methods(resp, payment_config: PagarmeFormConfig):
    assert_contains(resp, f"paymentMethods: '{payment_config.payments_methods}'")
