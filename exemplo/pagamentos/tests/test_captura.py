import pytest
import responses
from django.urls import reverse

TOKEN = 'test_transaction_aJx9ibUmRqYcQrrUaNtQ3arTO4tF1z'


@pytest.fixture
def pagarme_responses():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/transactions/{TOKEN}', json=transaction_resp)
        rsps.add(responses.POST, f'https://api.pagar.me/1/transactions/{TOKEN}/capture', json=captura_resp)
        yield rsps


@pytest.fixture
def resp(client, pagarme_responses):
    return client.post(reverse('pagamentos:captura'), {'token': TOKEN})


def test_status_code(resp):
    assert resp.status_code == 200


@pytest.fixture
def pagarme_invalid_responses():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/transactions/{TOKEN}', json=transaction_resp_menor_que_minimo)

        yield rsps


@pytest.fixture
def resp_invalido(client, pagarme_invalid_responses):
    return client.post(reverse('pagamentos:captura'), {'token': TOKEN})


def test_status_code_invalid_value(resp_invalido):
    assert resp_invalido.status_code == 400


transaction_resp = {
    'object': 'transaction', 'status': 'authorized', 'refuse_reason': None, 'status_reason': 'antifraud',
    'acquirer_response_code': '0000', 'acquirer_name': 'pagarme', 'acquirer_id': '5cdec7071458b442125d940b',
    'authorization_code': '727706', 'soft_descriptor': None, 'tid': 7656619, 'nsu': 7656619,
    'date_created': '2020-01-21T01:10:13.015Z', 'date_updated': '2020-01-21T01:10:13.339Z', 'amount': 8000,
    'authorized_amount': 8000, 'paid_amount': 0, 'refunded_amount': 0, 'installments': 1, 'id': 7656619, 'cost': 70,
    'card_holder_name': 'Bar Baz', 'card_last_digits': '1111', 'card_first_digits': '411111', 'card_brand': 'visa',
    'card_pin_mode': None, 'card_magstripe_fallback': False, 'cvm_pin': False, 'postback_url': None,
    'payment_method': 'credit_card', 'capture_method': 'ecommerce', 'antifraud_score': None, 'boleto_url': None,
    'boleto_barcode': None, 'boleto_expiration_date': None, 'referer': 'encryption_key', 'ip': '177.27.238.139',

}

transaction_resp_menor_que_minimo = {
    'object': 'transaction', 'status': 'authorized', 'refuse_reason': None, 'status_reason': 'antifraud',
    'acquirer_response_code': '0000', 'acquirer_name': 'pagarme', 'acquirer_id': '5cdec7071458b442125d940b',
    'authorization_code': '727706', 'soft_descriptor': None, 'tid': 7656619, 'nsu': 7656619,
    'date_created': '2020-01-21T01:10:13.015Z', 'date_updated': '2020-01-21T01:10:13.339Z', 'amount': 800,
    'authorized_amount': 800, 'paid_amount': 0, 'refunded_amount': 0, 'installments': 1, 'id': 7656619, 'cost': 70,
    'card_holder_name': 'Bar Baz', 'card_last_digits': '1111', 'card_first_digits': '411111', 'card_brand': 'visa',
    'card_pin_mode': None, 'card_magstripe_fallback': False, 'cvm_pin': False, 'postback_url': None,
    'payment_method': 'credit_card', 'capture_method': 'ecommerce', 'antifraud_score': None, 'boleto_url': None,
    'boleto_barcode': None, 'boleto_expiration_date': None, 'referer': 'encryption_key', 'ip': '177.27.238.139',

}

captura_resp = {
    'object': 'transaction', 'status': 'paid', 'refuse_reason': None, 'status_reason': 'acquirer',
    'acquirer_response_code': '0000', 'acquirer_name': 'pagarme', 'acquirer_id': '5cdec7071458b442125d940b',
    'authorization_code': '408324', 'soft_descriptor': None, 'tid': 7656690, 'nsu': 7656690,
    'date_created': '2020-01-21T01:45:57.309Z', 'date_updated': '2020-01-21T01:47:27.105Z', 'amount': 8000,
    'authorized_amount': 8000, 'paid_amount': 8000, 'refunded_amount': 0, 'installments': 1, 'id': 7656690, 'cost': 100,
    'card_holder_name': 'agora captura', 'card_last_digits': '1111', 'card_first_digits': '411111',
    'card_brand': 'visa', 'card_pin_mode': None, 'card_magstripe_fallback': False, 'cvm_pin': False,
    'postback_url': None, 'payment_method': 'credit_card', 'capture_method': 'ecommerce', 'antifraud_score': None,
    'boleto_url': None, 'boleto_barcode': None, 'boleto_expiration_date': None, 'referer': 'encryption_key',
    'ip': '177.27.238.139', 'subscription_id': None, 'phone': None, 'address': None, 'customer': {
        'object': 'customer', 'id': 2601905, 'external_id': 'captura@gmail.com', 'type': 'individual', 'country': 'br',
        'document_number': None, 'document_type': 'cpf', 'name': 'Agora Captura', 'email': 'captura@gmail.com',
        'phone_numbers': ['+5512997411854'], 'born_at': None, 'birthday': None, 'gender': None,
        'date_created': '2020-01-21T01:45:57.228Z', 'documents': [
            {'object': 'document', 'id': 'doc_ck5n7vta0010nr36d01k1zzzw', 'type': 'cpf', 'number': '29770166863'}]
    }, 'billing': {
        'object': 'billing', 'id': 1135539, 'name': 'Agora Captura', 'address': {
            'object': 'address', 'street': 'Rua Bahamas', 'complementary': 'Sem complemento', 'street_number': '56',
            'neighborhood': 'Cidade Vista Verde', 'city': 'São José dos Campos', 'state': 'SP', 'zipcode': '12223770',
            'country': 'br', 'id': 2559019
        }
    }, 'shipping': None, 'items': [{
        'object': 'item', 'id': '1', 'title': 'Cadeira', 'unit_price': 8000,
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
