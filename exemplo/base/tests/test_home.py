import pytest
from django.urls import reverse


@pytest.fixture
def resp(client):
    return client.get(reverse('home'))


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
    resp = client.post(reverse('home'), dct)
    assert resp.status_code == 302
    assert resp.url == '/checkout/pytools?name=Foo+Bar+Baz&email=foo%40email.com&phone=%2B5512999999999&modal=true'
