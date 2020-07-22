import pytest
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains, assert_templates_used, assert_templates_not_used
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


def _make_config(payment_config, slug, upsell=None):
    return baker.make(
        PagarmeItemConfig,
        slug=slug,
        tangible=False,
        default_config=payment_config,
        upsell=upsell
    )


@pytest.fixture
def payment_item(payment_config, upsell):
    return _make_config(payment_config, 'item-slug', upsell)


@pytest.fixture
def upsell(payment_config):
    return _make_config(payment_config, 'upsell-slug')


@pytest.fixture
def resp(client, payment_item):
    return client.get(reverse('django_pagarme:thanks', kwargs={'slug': payment_item.slug}))


def test_status_code(resp):
    assert resp.status_code == 200


def test_payment_item_available_on_context(resp, payment_item):
    context_payment_item = resp.context['payment_item_config']
    assert payment_item == context_payment_item


def test_thanks_fallback_used(resp, payment_item):
    assert_templates_used(resp, 'django_pagarme/thanks.html')
    assert_templates_not_used(resp, 'django_pagarme/thanks_item_slug.html')


def test_upsell_one_click(resp, upsell):
    assert_contains(resp, reverse('django_pagarme:one_click', kwargs={'slug': upsell.slug}))


def test_thanks_with_slug_suffix_used(client, upsell):
    resp = client.get(reverse('django_pagarme:thanks', kwargs={'slug': upsell.slug}))
    assert_templates_not_used(resp, 'django_pagarme/thanks.html')
    assert_templates_used(resp, 'django_pagarme/thanks_upsell_slug.html')
