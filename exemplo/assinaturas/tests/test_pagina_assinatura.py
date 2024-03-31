import pytest
from django.urls import reverse
from django.utils.http import urlencode
from model_bakery import baker

from django_assertions import assert_contains, assert_not_contains, assert_templates_used, assert_templates_not_used
from django_pagarme.models import Plan, UserPaymentProfile


@pytest.fixture
def plan(db):
    return baker.make(Plan, name='Sample Plan', amount=4990, payment_methods='credit_card')


@pytest.fixture
def resp(client, plan):
    return client.get(reverse('django_pagarme:subscription', kwargs={'slug': plan.slug}))


def test_status_code(plan: Plan, resp):
    assert resp.status_code == 200


def test_fall_back_template(resp, plan):
    assert_templates_used(resp, 'django_pagarme/subscription.html')
    assert_templates_not_used(resp, 'django_pagarme/subscription_sample_plan.html')


def test_pagarme_javascript(resp):
    assert_contains(resp, 'script src="//assets.pagar.me/checkout/1.1.0/checkout.js"')


def test_encription_key_is_present(settings, resp):
    assert_contains(resp, settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA)


def test_amount(resp, plan: Plan):
    assert_contains(resp, f"amount: {plan.amount}")


def test_payment_methods(resp, plan: Plan):
    assert_contains(resp, f"paymentMethods: '{plan.payment_methods}'")


def test_not_open_modal(resp):
    assert_not_contains(resp, '$button.click()')


@pytest.fixture
def resp_open_modal(client, plan):
    path = reverse('django_pagarme:subscription', kwargs={'slug': plan.slug})
    query_string = urlencode({'open_modal': True})
    return client.get(f'{path}?{query_string}')


def test_modal_open(resp_open_modal):
    assert_contains(resp_open_modal, 'setTimeout(initiateCheckout, 1000);')


@pytest.fixture
def customer_query_string_data():
    return {'name': 'qs_name', 'email': 'qs@email.com', 'phone': '+5512999999999'}


@pytest.fixture
def resp_customer_on_query_string(client, plan, customer_query_string_data):
    path = reverse('django_pagarme:subscription', kwargs={'slug': plan.slug})
    query_string = urlencode(customer_query_string_data)
    return client.get(f'{path}?{query_string}')


def test_customer_data_on_form(resp_customer_on_query_string, customer_query_string_data):
    for v in customer_query_string_data.values():
        assert_contains(resp_customer_on_query_string, v)


@pytest.fixture
def logged_user(django_user_model):
    return baker.make(django_user_model)


@pytest.fixture
def resp_logged_user(client, plan, logged_user):
    client.force_login(logged_user)
    path = reverse('django_pagarme:subscription', kwargs={'slug': plan.slug})
    return client.get(path)


def test_user_data_on_form(resp_logged_user, logged_user):
    data = {
        'external_id': str(logged_user.id),
        'name': logged_user.first_name,
        'email': logged_user.email,
    }
    for k, v in data.items():
        assert_contains(resp_logged_user, f"{k}: '{v}'")


@pytest.fixture
def resp_logged_user_and_customer_qs(client, plan, logged_user, customer_query_string_data):
    client.force_login(logged_user)
    path = reverse('django_pagarme:subscription', kwargs={'slug': plan.slug})
    query_string = urlencode(customer_query_string_data)
    return client.get(f'{path}?{query_string}')


def test_customer_qs_precedes_logged_user(resp_logged_user_and_customer_qs, logged_user, customer_query_string_data):
    data = {
        'external_id': str(logged_user.id),
    }
    data.update(customer_query_string_data)
    for k, v in data.items():
        if k != 'phone':
            assert_contains(resp_logged_user_and_customer_qs, f"{k}: '{v}'")
        else:
            assert_contains(resp_logged_user_and_customer_qs, v)


@pytest.fixture
def payment_profile(logged_user):
    return baker.make(UserPaymentProfile, phone='+5512999999999', user=logged_user)


@pytest.fixture
def resp_logged_user_with_payment_profile(client, plan, logged_user, payment_profile):
    client.force_login(logged_user)
    path = reverse('django_pagarme:subscription', kwargs={'slug': plan.slug})
    return client.get(path)


def test_payment_profile_precedes_logged_user(resp_logged_user_with_payment_profile,
                                              payment_profile: UserPaymentProfile):
    assert_contains(resp_logged_user_with_payment_profile, str(payment_profile.phone))
    assert_contains(resp_logged_user_with_payment_profile, payment_profile.name)
    assert_contains(resp_logged_user_with_payment_profile, payment_profile.document_number)
    assert_contains(resp_logged_user_with_payment_profile, payment_profile.document_type)
    assert_contains(resp_logged_user_with_payment_profile, payment_profile.customer_type)
