import json

import pytest
import responses
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains, assert_templates_used, assert_templates_not_used
from django_pagarme import facade
from django_pagarme.models import Plan, PagarmePayment, Subscription


@pytest.fixture
def plan(db):
    return baker.make(
        Plan, name='Sample Plan', slug='sample-plan', amount=5000, payment_methods='boleto', pagarme_id=123
    )


@pytest.fixture
def pagarme_responses(subscription_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, f'https://api.pagar.me/1/subscriptions', json=subscription_json)
        yield rsps


@pytest.fixture
def resp(client, pagarme_responses, plan, subscription_json):
    path = reverse('django_pagarme:subscribe', kwargs={'slug': plan.slug})
    data = {
        'payment_method': 'boleto',
        'installments': None,
        'amount': 49000,
        'customer': {
            'name': 'Zé',
            'email': 'admin@example.com',
            'document_number': '17911211019',
            'phone': {
                'ddd': '11',
                'number': '48157549'
            },
            'address': {
                'zipcode': '57052575',
                'street': 'Rua Jacarandá',
                'street_number': '123',
                'complementary': '',
                'neighborhood': 'Gruta de Lourdes',
                'city': 'Maceió',
                'state': 'AL'
            }
        },
    }
    return client.post(path, json.dumps(data), xhr=True, content_type='application/x-www-form-urlencoded')


def test_status_code(resp):
    assert resp.status_code == 200


def test_pagarme_payment_creation(resp):
    assert PagarmePayment.objects.exists()


def test_subscription_creation(resp):
    assert Subscription.objects.exists()


def test_pagarme_payment_data(resp, subscription_json, plan: Plan):
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
        [],
        str(subscription_json['current_transaction']['id']),
        BOLETO_BARCODE,
        BOLETO_URL
    )


TRANSACTION_ID = 9881783
SUBSCTIPTION_ID = 523738

BOLETO_URL = 'www.some.boleto.com'
BOLETO_BARCODE = '123455'


@pytest.fixture
def subscription_json(plan: Plan):
    return {
        'object': 'subscription',
        'plan': {
            'object': 'plan',
            'id':  plan.pagarme_id,
            'amount':  plan.amount,
            'days':  plan.days,
            'name':  plan.name,
            'trial_days':  plan.trial_days,
            'date_created': '2020-09-27T17:17:37.662Z',
            'payment_methods':  plan.payment_methods.split(),
            'color':  None,
            'charges':  plan.charges,
            'installments':  1,
            'invoice_reminder':  None,
            'payment_deadline_charges_interval':  1
        },
        'id':  SUBSCTIPTION_ID,
        'current_transaction': {
            'object': 'transaction',
            'status': 'waiting_payment',
            'refuse_reason': None,
            'status_reason': 'acquirer',
            'acquirer_response_code': None,
            'acquirer_name': 'pagarme',
            'acquirer_id': '5f2da8e6d6f8614925b7cbc8',
            'authorization_code': None,
            'soft_descriptor': None,
            'tid': TRANSACTION_ID,
            'nsu': TRANSACTION_ID,
            'date_created': '2020-09-27T17:46:36.479Z',
            'date_updated': '2020-09-27T17:46:36.880Z',
            'amount': 5000,
            'authorized_amount': 5000,
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
            'postback_url': None,
            'payment_method': 'boleto',
            'capture_method': 'ecommerce',
            'antifraud_score': None,
            'boleto_url': BOLETO_URL,
            'boleto_barcode': BOLETO_BARCODE,
            'boleto_expiration_date': '2020-10-04T03:00:00.000Z',
            'referer': 'api_key',
            'ip': '187.56.250.47',
            'subscription_id': SUBSCTIPTION_ID,
            'metadata': {

            },
            'antifraud_metadata': {

            },
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
        },
        'postback_url': 'https://4ae45fb5782424f3b73b27e3586478d2.m.pipedream.net',
        'payment_method': 'boleto',
        'card_brand': None,
        'card_last_digits': None,
        'current_period_start': None,
        'current_period_end': None,
        'charges': 0,
        'soft_descriptor': None,
        'status': 'unpaid',
        'date_created': '2020-09-27T17:46:36.864Z',
        'date_updated': '2020-09-27T17:46:36.864Z',
        'phone': {
            'object': 'phone',
            'ddi': '55',
            'ddd': '11',
            'number': '48157549',
            'id': 794725
        },
        'address': {
            'object': 'address',
            'street': 'Rua Jacarandá',
            'complementary': '',
            'street_number': '123',
            'neighborhood': 'Gruta de Lourdes',
            'city': 'Maceió',
            'state': 'AL',
            'zipcode': '57052575',
            'country': 'Brasil',
            'id': 3434272
        },
        'customer': {
            'object': 'customer',
            'id': 3809673,
            'external_id': None,
            'type': None,
            'country': None,
            'document_number': '17911211019',
            'document_type': 'cpf',
            'name': 'Zé',
            'email': 'admin@example.com',
            'phone_numbers': None,
            'born_at': None,
            'birthday': None,
            'gender': None,
            'date_created': '2020-09-27T17:46:36.410Z',
            'documents': [

            ]
        },
        'card': None,
        'metadata': None,
        'fine': {

        },
        'interest': {

        },
        'settled_charges': None,
        'manage_token': 'some-token',
        'manage_url': 'https://httpbin.org/'
    }
