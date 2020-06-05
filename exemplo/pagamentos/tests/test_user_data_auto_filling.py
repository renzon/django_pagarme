import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from django_assertions import assert_contains
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig, UserPaymentProfile


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
def logged_user(django_user_model):
    return baker.make(django_user_model, is_active=True,  _fill_optional=True)


@pytest.fixture
def payment_profile(logged_user):
    return baker.make(UserPaymentProfile, phone='+5512999999999', user=logged_user)


@pytest.fixture
def client_absent_profile_with_user(logged_user, client: Client):
    client.force_login(logged_user)
    return client


@pytest.fixture
def client_with_payment_profile(logged_user, client: Client, payment_profile):
    client.force_login(logged_user)
    return client


@pytest.fixture
def resp_absent_user(client, payment_item):
    return client.get(reverse('django_pagarme:contact_info', kwargs={'slug': payment_item.slug}))


def test_status_code_absent_user(resp_absent_user):
    assert 200 == resp_absent_user.status_code


@pytest.fixture
def resp_absent_profile_with_user(client_absent_profile_with_user, payment_item):
    return client_absent_profile_with_user.get(
        reverse('django_pagarme:contact_info', kwargs={'slug': payment_item.slug}))


def test_logged_user_email_is_present(resp_absent_profile_with_user, logged_user):
    assert_contains(resp_absent_profile_with_user, logged_user.email)


def test_logged_user_first_name_is_present(resp_absent_profile_with_user, logged_user):
    assert_contains(resp_absent_profile_with_user, logged_user.first_name)


@pytest.fixture
def resp_with_payment_profile(client_with_payment_profile, payment_item):
    return client_with_payment_profile.get(
        reverse('django_pagarme:contact_info', kwargs={'slug': payment_item.slug}))


def test_profile_email_is_present(resp_with_payment_profile, payment_profile):
    assert_contains(resp_with_payment_profile, payment_profile.email)


def test_profile_first_name_is_present(resp_with_payment_profile, payment_profile):
    assert_contains(resp_with_payment_profile, payment_profile.name)


def test_profile_phone_is_present(resp_with_payment_profile, payment_profile):
    assert_contains(resp_with_payment_profile, payment_profile.phone)
