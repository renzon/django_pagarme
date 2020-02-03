import pytest
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains
from django_pagarme.models import Sellable, SellableOption


@pytest.fixture
def sellable_option(db):
    return baker.make(SellableOption)


@pytest.fixture
def sellable(sellable_option):
    return baker.make(Sellable, default_option=sellable_option)


@pytest.fixture
def resp(client, sellable):
    return client.get(reverse('pagamentos:produto', kwargs={'slug': sellable.slug}))


def test_status_code(sellable: Sellable, resp):
    assert resp.status_code == 200


def test_pagarme_javascript(resp):
    assert_contains(resp, 'script src="//assets.pagar.me/checkout/1.1.0/checkout.js"')


def test_encription_key_is_present(settings, resp):
    assert_contains(resp, settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA)


def test_price(resp, sellable: Sellable):
    assert_contains(resp, f"amount: {sellable.price}")


def test_unit_price(resp, sellable: Sellable):
    assert_contains(resp, f"unit_price: {sellable.price}")


def test_max_installments(resp, sellable_option: SellableOption):
    assert_contains(resp, f'maxInstallments: {sellable_option.max_installments}')


def test_default_installment(resp, sellable_option: SellableOption):
    assert_contains(resp, f'defaultInstallment: {sellable_option.default_installment}')


def test_free_installment(resp, sellable_option: SellableOption):
    assert_contains(resp, f'freeInstallments: {sellable_option.free_installment}')


def test_interest_rate(resp, sellable_option: SellableOption):
    assert_contains(resp, f'interestRate: {sellable_option.interest_rate:.2f}')


def test_slug(resp, sellable: Sellable):
    assert_contains(resp, f"id: '{sellable.slug}'")


def test_name(resp, sellable: Sellable):
    assert_contains(resp, f"title: '{sellable.name}'")


def test_tangible(resp, sellable: Sellable):
    assert_contains(resp, f"tangible: '{str(sellable.tangible).lower()}'")


def test_payment_methods(resp, sellable_option: SellableOption):
    assert_contains(resp, f"paymentMethods: '{sellable_option.payments_methods}'")
