import pytest
import responses
from django.core.management import call_command
from model_bakery import baker

from django_pagarme.models import Plan


@pytest.fixture
def pagarme_response(all_plans_json):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f'https://api.pagar.me/1/plans', json=all_plans_json)
        yield rsps


def test_should_sync_plans(db, pagarme_response):
    call_command('django_pagarme_sync_plans')
    assert Plan.objects.count() == 3


def test_should_not_recreate_the_same_plans(db, all_plans_json, pagarme_response):
    _ = [_make_plan(plan) for plan in all_plans_json]
    call_command('django_pagarme_sync_plans')
    assert Plan.objects.count() == 3


def test_should_remove_orphan_plans(db, all_plans_json, pagarme_response):
    _ = [_make_plan(plan) for plan in all_plans_json]
    baker.make(Plan, pagarme_id='some-inexistent-id')
    call_command('django_pagarme_sync_plans')
    assert Plan.objects.count() == 3


def _make_plan(plan):
    return baker.make(
        Plan,
        pagarme_id=plan['id'],
        amount=plan['amount'],
        days=plan['days'],
        name=plan['name'],
        trial_days=plan['trial_days'],
        payment_methods=','.join(plan['payment_methods']),
        charges=plan['charges'],
        invoice_reminder=plan['invoice_reminder'],
    )


@pytest.fixture
def all_plans_json():
    return [
        {
            'object': 'plan',
            'id': 504039,
            'amount': 49000,
            'days': 30,
            'name': 'Plan A',
            'trial_days': 0,
            'date_created': '2020-09-23T03:03:36.459Z',
            'payment_methods': [
                'credit_card'
            ],
            'color': None,
            'charges': 11,
            'installments': 1,
            'invoice_reminder': None,
            'payment_deadline_charges_interval': 1
        },
        {
            'object': 'plan',
            'id': 504038,
            'amount': 32000,
            'days': 30,
            'name': 'Plan B',
            'trial_days': 0,
            'date_created': '2020-09-23T03:03:00.139Z',
            'payment_methods': [
                'boleto'
            ],
            'color': None,
            'charges': 11,
            'installments': 1,
            'invoice_reminder': None,
            'payment_deadline_charges_interval': 1
        },
        {
            'object': 'plan',
            'id': 504037,
            'amount': 38000,
            'days': 30,
            'name': 'Plan C',
            'trial_days': 0,
            'date_created': '2020-09-23T03:01:26.365Z',
            'payment_methods': [
                'credit_card',
                'boleto'
            ],
            'color': None,
            'charges': 3,
            'installments': 1,
            'invoice_reminder': None,
            'payment_deadline_charges_interval': 1
        }
    ]
