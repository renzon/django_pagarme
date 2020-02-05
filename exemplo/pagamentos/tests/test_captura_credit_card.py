import pytest
import responses
from django.urls import reverse
from model_bakery import baker

from django_pagarme.models import PagarmePayment, PaymentConfig, PaymentItem

TOKEN = 'test_transaction_aJx9ibUmRqYcQrrUaNtQ3arTO4tF1z'


@pytest.fixture
def payment_config(db):
    return baker.make(
        PaymentConfig,
        max_installments=12,
        free_installment=1,
        interest_rate=1.66,
        payments_methods='credit_card'
    )


def test_calculate_amount(payment_config):
    assert payment_config.calculate_amount(9999, 12) == 11991


@pytest.fixture
def payment_item(payment_config):
    return baker.make(
        PaymentItem,
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


def test_success_msg(resp, payment_item: PaymentItem):
    assert resp.json() == {
        'payment_method': 'credit_card',
        'amount': payment_item.price
    }


def test_pagarme_payment_creation(resp):
    assert PagarmePayment.objects.exists()


def test_pagarme_payment_data(resp, transaction_json, payment_item: PaymentItem):
    payment = PagarmePayment.objects.first()
    assert (
               payment.card_id,
               payment.card_last_digits,
               payment.installments,
               list(payment.items.all()),
           ) == (
               transaction_json['card']['id'],
               transaction_json['card_last_digits'],
               transaction_json['installments'],
               [payment_item],
           )


def _invalid_resp(tampered_item_price_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/transactions/{TOKEN}', json=tampered_item_price_json)
        yield rsps


# Testing tampered item price

@pytest.fixture
def tampered_item_price_json(transaction_json, payment_item: PaymentItem):
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
def tampered_authorized_amount_json(transaction_json, payment_item: PaymentItem):
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
def tampered_installments_json(transaction_json, payment_config: PaymentConfig):
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


def test_installments_error_msg(resp_tampered_installments, tampered_installments_json, payment_config: PaymentConfig):
    installments = tampered_installments_json['installments']
    assert resp_tampered_installments.json() == {
        'errors': f'Parcelamento em {installments} vez(es) é maior que o máximo {payment_config.max_installments}'
    }


# Test tampered interest)rate:

@pytest.fixture
def tampered_interest_rate_json(transaction_json, payment_config: PaymentConfig):
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


@pytest.fixture
def transaction_json(payment_item: PaymentItem):
    return {
        'object': 'transaction', 'status': 'authorized', 'refuse_reason': None, 'status_reason': 'antifraud',
        'acquirer_response_code': '0000', 'acquirer_name': 'pagarme', 'acquirer_id': '5cdec7071458b442125d940b',
        'authorization_code': '727706', 'soft_descriptor': None, 'tid': 7656619, 'nsu': 7656619,
        'date_created': '2020-01-21T01:10:13.015Z', 'date_updated': '2020-01-21T01:10:13.339Z',
        'amount': payment_item.price,
        'authorized_amount': payment_item.price, 'paid_amount': 0, 'refunded_amount': 0, 'installments': 1,
        'id': 7656619, 'cost': 70,
        'card_holder_name': 'Bar Baz', 'card_last_digits': '1111', 'card_first_digits': '411111', 'card_brand': 'visa',
        'card_pin_mode': None, 'card_magstripe_fallback': False, 'cvm_pin': False, 'postback_url': None,
        'payment_method': 'credit_card', 'capture_method': 'ecommerce', 'antifraud_score': None, 'boleto_url': None,
        'boleto_barcode': None, 'boleto_expiration_date': None, 'referer': 'encryption_key', 'ip': '177.27.238.139',
        'items': [{
            'object': 'item',
            'id': f'{payment_item.slug}',
            'title': f'{payment_item.name}',
            'unit_price': payment_item.price,
            'quantity': 1, 'category': None, 'tangible': False, 'venue': None, 'date': None
        }], 'card': {
            'object': 'card', 'id': 'card_ck5n7vtbi010or36dojq96sb1', 'date_created': '2020-01-21T01:45:57.294Z',
            'date_updated': '2020-01-21T01:45:57.789Z', 'brand': 'visa', 'holder_name': 'agora captura',
            'first_digits': '411111', 'last_digits': '1111', 'country': 'UNITED STATES',
            'fingerprint': 'cj5bw4cio00000j23jx5l60cq', 'valid': True, 'expiration_date': '1227'
        }

    }


@pytest.fixture
def captura_json(payment_item: PaymentItem):
    return {
        'object': 'transaction', 'status': 'paid', 'refuse_reason': None, 'status_reason': 'acquirer',
        'acquirer_response_code': '0000', 'acquirer_name': 'pagarme', 'acquirer_id': '5cdec7071458b442125d940b',
        'authorization_code': '408324', 'soft_descriptor': None, 'tid': 7656690, 'nsu': 7656690,
        'date_created': '2020-01-21T01:45:57.309Z', 'date_updated': '2020-01-21T01:47:27.105Z', 'amount': 8000,
        'authorized_amount': payment_item.price,
        'paid_amount': payment_item.price, 'refunded_amount': 0,
        'installments': 1,
        'id': 7656690,
        'cost': 100,
        'card_holder_name': 'agora captura', 'card_last_digits': '1111', 'card_first_digits': '411111',
        'card_brand': 'visa', 'card_pin_mode': None, 'card_magstripe_fallback': False, 'cvm_pin': False,
        'postback_url': None,
        'payment_method': 'credit_card', 'capture_method': 'ecommerce', 'antifraud_score': None,
        'boleto_url': None, 'boleto_barcode': None, 'boleto_expiration_date': None, 'referer': 'encryption_key',
        'ip': '177.27.238.139', 'subscription_id': None, 'phone': None, 'address': None,
        'customer': {
            'object': 'customer', 'id': 2601905, 'external_id': 'captura@gmail.com', 'type': 'individual',
            'country': 'br',
            'document_number': None, 'document_type': 'cpf', 'name': 'Agora Captura', 'email': 'captura@gmail.com',
            'phone_numbers': ['+5512997411854'], 'born_at': None, 'birthday': None, 'gender': None,
            'date_created': '2020-01-21T01:45:57.228Z', 'documents': [
                {'object': 'document', 'id': 'doc_ck5n7vta0010nr36d01k1zzzw', 'type': 'cpf', 'number': '29770166863'}]
        }, 'billing': {
            'object': 'billing', 'id': 1135539, 'name': 'Agora Captura', 'address': {
                'object': 'address', 'street': 'Rua Bahamas', 'complementary': 'Sem complemento', 'street_number': '56',
                'neighborhood': 'Cidade Vista Verde', 'city': 'São José dos Campos', 'state': 'SP',
                'zipcode': '12223770',
                'country': 'br', 'id': 2559019
            }
        }, 'shipping': None,
        'items': [{
            'object': 'item',
            'id': f'{payment_item.slug}',
            'title': f'{payment_item.name}',
            'unit_price': payment_item.price,
            'quantity': 1, 'category': None, 'tangible': False, 'venue': None, 'date': None
        }], 'card': {
            'object': 'card', 'id': 'card_ck5n7vtbi010or36dojq96sb1', 'date_created': '2020-01-21T01:45:57.294Z',
            'date_updated': '2020-01-21T01:45:57.789Z', 'brand': 'visa', 'holder_name': 'agora captura',
            'first_digits': '411111', 'last_digits': '1111', 'country': 'UNITED STATES',
            'fingerprint': 'cj5bw4cio00000j23jx5l60cq', 'valid': True, 'expiration_date': '1227'
        }, 'split_rules': None, 'metadata': {}, 'antifraud_metadata': {}, 'reference_key': None, 'device': None,
        'local_transaction_id': None, 'local_time': None, 'fraud_covered': False, 'fraud_reimbursed': None,
        'order_id': None, 'risk_level': 'very_low', 'receipt_url': None, 'payment': None, 'addition': None,
        'discount': None, 'private_label': None
    }
