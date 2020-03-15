import pytest
from django.urls import reverse

from django_assertions import assert_contains


@pytest.fixture
def resp(client):
    return client.get(reverse('django_pagarme:contact_info', kwargs={'slug': 'pytools'}))


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
def test_valid_phones(client, phone):
    dct = {'name': 'Foo Bar Baz', 'email': 'foo@email.com', 'phone': phone}
    resp = client.post(reverse('django_pagarme:contact_info', kwargs={'slug': 'pytools'}), dct)
    assert resp.status_code == 302
    assert resp.url == (
        '/checkout/pagarme/pytools?name=Foo+Bar+Baz&email=foo%40email.com&phone=%2B5512999999999&open_modal=true')


@pytest.mark.parametrize(
    'phone',
    [
        '999999999',
        '9',
        '99999999999999999999',
    ]
)
def test_invalid_phones(client, phone):
    email = 'foo'
    dct = {'name': 'Foo Bar Baz', 'email': email, 'phone': phone}
    resp = client.post(reverse('django_pagarme:contact_info', kwargs={'slug': 'pytools'}), dct)
    assert_contains(resp, phone, status_code=400)
    assert_contains(resp, email, status_code=400)
