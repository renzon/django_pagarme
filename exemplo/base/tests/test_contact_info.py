import pytest
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains
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
def active_payment_item_config(payment_config):
    return baker.make(
        PagarmeItemConfig,
        tangible=False,
        default_config=payment_config,
        deleted_at=None
    )


@pytest.fixture
def resp(client, active_payment_item_config):
    return client.get(reverse('django_pagarme:contact_info', kwargs={'slug': active_payment_item_config.slug}))


def test_status_code(resp):
    return resp.status_code == 200


@pytest.mark.parametrize(
    'phone',
    [
        '12999999999',
        '+5512999999999',
        '(+55) 12999999999',
        '(12) 9999-99999',
    ]
)
def test_valid_phones(client, phone, active_payment_item_config):
    dct = {'name': 'Foo Bar Baz', 'email': 'foo@email.com', 'phone': phone}
    slug = active_payment_item_config.slug
    resp = client.post(reverse('django_pagarme:contact_info', kwargs={'slug': slug}), dct)
    assert resp.status_code == 302
    assert resp.url == (
        f'/checkout/pagarme/{slug}?name=Foo+Bar+Baz&email=foo%40email.com&phone=%2B5512999999999&open_modal=true')


@pytest.mark.parametrize(
    'phone',
    [
        '999999999',
        '9',
        '99999999999999999999',
    ]
)
def test_invalid_phones(client, phone, active_payment_item_config):
    email = 'foo'
    dct = {'name': 'Foo Bar Baz', 'email': email, 'phone': phone}
    resp = client.post(reverse('django_pagarme:contact_info', kwargs={'slug': active_payment_item_config.slug}), dct)
    assert_contains(resp, phone, status_code=400)
    assert_contains(resp, email, status_code=400)
