import pytest
import responses
from django.urls import reverse
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig, PagarmePayment

TOKEN = 'test_transaction_hfBR0ysHX0NewkUJeXIstI4MdZDb2U'


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
def resp(client, pagarme_responses):
    return client.post(reverse('django_pagarme:capture'), {'token': TOKEN})


def test_status_code(resp):
    assert resp.status_code == 200


def test_success_msg(resp, payment_item: PagarmeItemConfig):
    assert resp.json() == {
        'payment_method': 'boleto',
        'amount': payment_item.price
    }


def test_pagarme_payment_creation(resp):
    assert PagarmePayment.objects.exists()


def test_pagarme_payment_data(resp, transaction_json, payment_item: PagarmeItemConfig):
    payment = PagarmePayment.objects.first()
    assert (
               payment.card_id,
               payment.card_last_digits,
               payment.installments,
               list(payment.items.all()),
               payment.transaction_id,
               payment.boleto_barcode,
               payment.boleto_url,

           ) == (
               None,
               None,
               1,
               [payment_item],
               str(transaction_json['id']),
               BOLETO_BARCODE,
               BOLETO_URL
           )


def test_pagarme_payment_initial_configuration(resp):
    payment = facade.find_payment(str(TRANSACTION_ID))
    assert [n.status for n in payment.notifications.all()] == [facade.AUTHORIZED]


def _invalid_resp(tampered_item_price_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/transactions/{TOKEN}', json=tampered_item_price_json)
        yield rsps


# Testing tampered item price

@pytest.fixture
def tampered_item_price_json(transaction_json, payment_item: PagarmeItemConfig):
    transaction_json['items'][0]['unit_price'] = payment_item.price - 1
    return transaction_json


@pytest.fixture
def pargarme_tampered_item_price_resps(tampered_item_price_json):
    yield from _invalid_resp(tampered_item_price_json)


@pytest.fixture
def resp_tampered_item_price(client, pargarme_tampered_item_price_resps):
    return client.post(reverse('django_pagarme:capture'), {'token': TOKEN})


def test_status_code_invalid_item_price(resp_tampered_item_price):
    assert resp_tampered_item_price.status_code == 400


def test_item_price_error_msg(resp_tampered_item_price, tampered_item_price_json, payment_item):
    unit_price = tampered_item_price_json['items'][0]['unit_price']
    assert resp_tampered_item_price.json() == {
        'errors': f'Valor de item {unit_price} é menor que o esperado {payment_item.price}'
    }


# Test tampered total amount price:

@pytest.fixture
def tampered_authorized_amount_json(transaction_json, payment_item: PagarmeItemConfig):
    transaction_json['authorized_amount'] = payment_item.price - 1
    return transaction_json


@pytest.fixture
def pargarme_tampered_authorized_amount_resps(tampered_authorized_amount_json):
    yield from _invalid_resp(tampered_authorized_amount_json)


@pytest.fixture
def resp_tampered_authorized_amount(client, pargarme_tampered_authorized_amount_resps):
    return client.post(reverse('django_pagarme:capture'), {'token': TOKEN})


def test_status_code_invalid_authorized_amount(resp_tampered_authorized_amount):
    assert resp_tampered_authorized_amount.status_code == 400


def test_authorized_amount_error_msg(resp_tampered_authorized_amount, tampered_authorized_amount_json, payment_item):
    authorized_amount = tampered_authorized_amount_json['authorized_amount']
    assert resp_tampered_authorized_amount.json() == {
        'errors': f'Valor autorizado {authorized_amount} é menor que o esperado {payment_item.price}'
    }


# Test tampered installments:

@pytest.fixture
def tampered_installments_json(transaction_json, payment_config: PagarmeFormConfig):
    transaction_json['installments'] = payment_config.max_installments + 1
    return transaction_json


@pytest.fixture
def pargarme_tampered_installments_resps(tampered_installments_json):
    yield from _invalid_resp(tampered_installments_json)


@pytest.fixture
def resp_tampered_installments(client, pargarme_tampered_installments_resps):
    return client.post(reverse('django_pagarme:capture'), {'token': TOKEN})


def test_status_code_invalid_installments(resp_tampered_installments):
    assert resp_tampered_installments.status_code == 400


def test_installments_error_msg(resp_tampered_installments, tampered_installments_json,
                                payment_config: PagarmeFormConfig):
    installments = tampered_installments_json['installments']
    assert resp_tampered_installments.json() == {
        'errors': f'Parcelamento em {installments} vez(es) é maior que o máximo {payment_config.max_installments}'
    }


# Test tampered interest)rate:

@pytest.fixture
def tampered_interest_rate_json(transaction_json, payment_config: PagarmeFormConfig):
    transaction_json['installments'] = 12  # Should charge interest and amount be 11991 and each installment 9.99
    return transaction_json


@pytest.fixture
def pargarme_tampered_interest_rate_resps(tampered_interest_rate_json):
    yield from _invalid_resp(tampered_interest_rate_json)


@pytest.fixture
def resp_tampered_interest_rate(client, pargarme_tampered_interest_rate_resps):
    return client.post(reverse('django_pagarme:capture'), {'token': TOKEN})


def test_status_code_invalid_interest_rate(resp_tampered_interest_rate):
    assert resp_tampered_interest_rate.status_code == 400


TRANSACTION_ID = 7956027

BOLETO_URL = 'www.some.boleto.com'
BOLETO_BARCODE = '123455'


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
