from django.urls import reverse

from django_assertions import assert_contains


def test_status_code(client):
    resp = client.get(reverse('pagamentos:produto'))
    assert resp.status_code == 200


def test_pagarme_javascript(client):
    resp = client.get(reverse('pagamentos:produto'))
    assert_contains(resp, 'script src="//assets.pagar.me/checkout/1.1.0/checkout.js"')

def test_encription_key_is_present(client, settings):
    resp = client.get(reverse('pagamentos:produto'))
    assert_contains(resp, settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA)
