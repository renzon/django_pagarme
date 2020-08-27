import pytest
import responses
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_redirects
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig, UserPaymentProfile

baker.generators.add('phonenumber_field.modelfields.PhoneNumberField', lambda: '00000000000')


@pytest.fixture
def payment_config(db):
    return baker.make(
        PagarmeFormConfig,
        max_installments=12,
        free_installment=1,
        interest_rate=1.66,
        payments_methods='credit_card'
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
def user_payment_profile():
    yield baker.make(UserPaymentProfile)


@pytest.fixture
def resp_get(client, payment_item):
    return client.get(reverse('django_pagarme:one_click', kwargs={'slug': payment_item.slug}))


def test_get_request_should_redirect_to_payment_item_page(resp_get, payment_item):
    assert_redirects(resp_get, reverse('django_pagarme:pagarme', kwargs={'slug': payment_item.slug}))


@pytest.fixture
def pagarme_responses(transaction_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, f'https://api.pagar.me/1/transactions', json=transaction_json)
        yield rsps


@pytest.fixture
def resp(client, pagarme_responses, payment_item, user_payment_profile):
    client.force_login(user_payment_profile.user)
    return client.post(reverse('django_pagarme:one_click', kwargs={'slug': payment_item.slug}))


def test_post_request_should_redirect_to_thank_you_page(resp, payment_item):
    assert_redirects(resp, reverse('django_pagarme:thanks', kwargs={'slug': payment_item.slug}))


TRANSACTION_ID = 7956027


@pytest.fixture
def transaction_json(payment_item: PagarmeItemConfig):
    return {
        'object': 'transaction',
        'status': 'authorized',
        'refuse_reason': None,
        'status_reason': 'acquirer',
        'acquirer_response_code': None,
        'acquirer_name': 'pagarme',
        'acquirer_id': '5cdec7071458b442125d940b',
        'authorization_code': None,
        'soft_descriptor': None,
        'tid': TRANSACTION_ID,
        'nsu': TRANSACTION_ID,
        'date_created': '2020-03-07T17:04:58.279Z',
        'date_updated': '2020-03-07T17:04:58.502Z',
        'authorized_amount': payment_item.price,
        'paid_amount': 0,
        'refunded_amount': 0,
        'installments': 1,
        'id': TRANSACTION_ID,
        'cost': 0,
        'card_holder_name': None,
        'card_last_digits': None,
        'card_first_digits': None,
        'card_brand': None,
        'card_pin_mode': None,
        'card_magstripe_fallback': False,
        'cvm_pin': False,
        'postback_url': 'https://e0f89dca.ngrok.io/django_pagarme/notification',
        'payment_method': 'boleto',
        'capture_method': 'ecommerce',
        'antifraud_score': None,
        'boleto_url': None,
        'boleto_barcode': None,
        'boleto_expiration_date': '2020-03-09T03:00:00.000Z',
        'referer': 'encryption_key',
        'ip': '177.170.213.5',
        'subscription_id': None,
        'phone': None,
        'address': None,
        'customer': {
            'object': 'customer',
            'id': 2725813,
            'external_id': 'foo@email.com',
            'type': 'individual',
            'country': 'br',
            'document_number': None,
            'document_type': 'cpf',
            'name': 'Foo',
            'email': 'foo@email.com',
            'phone_numbers': ['+5512999999999'],
            'born_at': None,
            'birthday': None,
            'gender': None,
            'date_created': '2020-03-07T17:04:58.220Z',
            'documents': [
                {
                    'object': 'document',
                    'id': 'doc_ck7huyv07072mmp6f59af8u8h',
                    'type': 'cpf',
                    'number': '04367331024'
                }]
        },
        'billing': {
            'object': 'billing',
            'id': 1168861,
            'name': 'Foo',
            'address': {
                'object': 'address',
                'street': 'Rua Buenos Aires',
                'complementary': 'Sem complemento',
                'street_number': '7',
                'neighborhood': 'Cidade Vista Verde',
                'city': 'São José dos Campos',
                'state': 'SP',
                'zipcode': '12223730',
                'country': 'br',
                'id': 2641028
            }
        },
        'shipping': None,
        'items': [{
            'object': 'item',
            'id': f'{payment_item.slug}',
            'title': f'{payment_item.name}',
            'unit_price': payment_item.price,
            'quantity': 1,
            'category': None,
            'tangible': False,
            'venue': None,
            'date': None
        }],
        'card': None,
        'split_rules': None,
        'metadata': {},
        'antifraud_metadata': {},
        'reference_key': None,
        'device': None,
        'local_transaction_id': None,
        'local_time': None,
        'fraud_covered': False,
        'fraud_reimbursed': None,
        'order_id': None,
        'risk_level': 'unknown',
        'receipt_url': None,
        'payment': None,
        'addition': None,
        'discount': None,
        'private_label': None
    }
