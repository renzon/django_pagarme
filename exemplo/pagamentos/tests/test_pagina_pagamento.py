import pytest
from django.urls import reverse
from django.utils.http import urlencode
from model_bakery import baker

from django_assertions import assert_contains, assert_not_contains
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig


@pytest.fixture
def payment_config(db):
    return baker.make(PagarmeFormConfig)


@pytest.fixture
def payment_item(payment_config):
    return baker.make(PagarmeItemConfig, default_config=payment_config)


@pytest.fixture
def resp(client, payment_item):
    return client.get(reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug}))


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


def test_not_open_modal(resp):
    assert_not_contains(resp, '$button.click()')


@pytest.fixture
def resp_open_modal(client, payment_item):
    path = reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug})
    query_string = urlencode({'open_modal': True})
    return client.get(f'{path}?{query_string}')


def test_modal_open(resp_open_modal):
    assert_contains(resp_open_modal, '$button.click()')


@pytest.fixture
def customer_query_string_data():
    return {'name': 'qs_name', 'email': 'qs@email.com', 'phone': '+5512999999999'}


@pytest.fixture
def resp_customer_on_query_string(client, payment_item, customer_query_string_data):
    path = reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug})
    query_string = urlencode(customer_query_string_data)
    return client.get(f'{path}?{query_string}')


def test_customer_data_on_form(resp_customer_on_query_string, customer_query_string_data):
    for v in customer_query_string_data.values():
        assert_contains(resp_customer_on_query_string, v)


@pytest.fixture
def logged_user(django_user_model):
    return baker.make(django_user_model)


@pytest.fixture
def resp_logged_user(client, payment_item, logged_user):
    client.force_login(logged_user)
    path = reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug})
    return client.get(path)


def test_user_data_on_form(resp_logged_user, logged_user):
    data = {
        'external_id': str(logged_user.id),
        'name': logged_user.first_name,
        'email': logged_user.email,
    }
    for k, v in data.items():
        assert_contains(resp_logged_user, f"{k}: '{v}'")


@pytest.fixture
def resp_logged_user_and_customer_qs(client, payment_item, logged_user, customer_query_string_data):
    client.force_login(logged_user)
    path = reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug})
    query_string = urlencode(customer_query_string_data)
    return client.get(f'{path}?{query_string}')


def test_customer_qs_precedes_logged_user(resp_logged_user_and_customer_qs, logged_user, customer_query_string_data):
    data = {
        'external_id': str(logged_user.id),
    }
    data.update(customer_query_string_data)
    for k, v in data.items():
        if k != 'phone':
            assert_contains(resp_logged_user_and_customer_qs, f"{k}: '{v}'")
        else:
            assert_contains(resp_logged_user_and_customer_qs, v)
