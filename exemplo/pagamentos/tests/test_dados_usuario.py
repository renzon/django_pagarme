import pytest
import responses
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig, PagarmePayment

TOKEN = 'test_transaction_hfBR0ysHX0NewkUJeXIstI4MdZDb2U'

@pytest.fixture
def logged_user(django_user_model):
    return baker.make(django_user_model)
@pytest.fixture
def client_with_user(logged_user, client:Client):
    client.force_login(logged_user)
    return client


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
def payment_item(payment_config):
    return baker.make(
        PagarmeItemConfig,
        tangible=False,
        default_config=payment_config
    )


@pytest.fixture
def pagarme_responses(transaction_json, captura_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/transactions/{TOKEN}', json=transaction_json)
        rsps.add(responses.POST, f'https://api.pagar.me/1/transactions/{TOKEN}/capture', json=captura_json)
        yield rsps


@pytest.fixture
def resp(client_with_user, pagarme_responses):
    return client_with_user.post(reverse('django_pagarme:capture'), {'token': TOKEN})



TRANSACTION_ID = 7956027

BOLETO_URL = 'www.some.boleto.com'
BOLETO_BARCODE = '123455'

STREET = 'Rua Buenos Aires'
COMPLEMENTARY = 'Sem complemento'
STREET_NUMBER = '7'
NEIGHBORHOOD = 'Cidade Vista Verde'
CITY = 'São José dos Campos'
STATE = 'SP'
ZIPCODE = '12223730'
COUNTRY = 'br'


@pytest.fixture
def transaction_json(payment_item: PagarmeItemConfig, logged_user):
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
            'external_id': f'{logged_user.id}',
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


@pytest.fixture
def captura_json(payment_item: PagarmeItemConfig):
    return {
        'object': 'transaction',
        'status': 'waiting_payment',
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
        'date_updated': '2020-03-07T17:11:14.957Z',
        'amount': payment_item.price,
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
        'boleto_url': BOLETO_URL,
        'boleto_barcode': BOLETO_BARCODE,
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
                    'number': '29770166863'
                }]
        },
        'billing': {
            'address': {
                'street': STREET,
                'complementary': COMPLEMENTARY,
                'street_number': STREET_NUMBER ,
                'neighborhood': NEIGHBORHOOD ,
                'city': CITY ,
                'state': STATE ,
                'zipcode': ZIPCODE ,
                'country': COUNTRY ,
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
