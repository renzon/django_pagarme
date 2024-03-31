import binascii
import hmac
from _sha1 import sha1

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmePayment, Plan, Subscription

TRANSACTION_ID = 7789955
SUBSCRIPTION_ID = 526141
PLAN_ID = 506330


@pytest.fixture
def plan(db):
    return baker.make(Plan, payment_methods='credit_card', pagarme_id=str(PLAN_ID))


@pytest.fixture
def subscription(plan):
    return baker.make(
        Subscription,
        initial_status='paid',
        pagarme_id=str(SUBSCRIPTION_ID),
        plan=plan,
        payment_method='credit_card'
    )


@pytest.fixture
def pagarme_payment(subscription):
    payment = baker.make(PagarmePayment, transaction_id=str(TRANSACTION_ID))
    payment.subscription = subscription
    payment.save()
    return payment


@pytest.fixture
def subscription_status_listener(mocker):
    mock = mocker.Mock()
    facade.add_subscription_status_changed(mock)
    yield mock
    facade._subscription_status_changed_listeners.pop()


@pytest.fixture
def raw_post(plan: Plan, subscription: Subscription, pagarme_payment: PagarmePayment):
    # noqa
    return f'id={subscription.pagarme_id}&fingerprint=1fbe60cafc6c0591c7d8ea37c186a7fa593daf83&event=subscription_status_changed&old_status=unpaid&desired_status=paid&current_status=trial&object=subscription&subscription%5Bobject%5D=subscription&subscription%5Bplan%5D%5Bobject%5D=plan&subscription%5Bplan%5D%5Bid%5D={plan.pagarme_id}&subscription%5Bplan%5D%5Bamount%5D=5000&subscription%5Bplan%5D%5Bdays%5D=1&subscription%5Bplan%5D%5Bname%5D=Teste&subscription%5Bplan%5D%5Btrial_days%5D=0&subscription%5Bplan%5D%5Bdate_created%5D=2020-09-27T17:17:37.662Z&subscription%5Bplan%5D%5Bpayment_methods%5D%5B0%5D=boleto&subscription%5Bplan%5D%5Bpayment_methods%5D%5B1%5D=credit_card&subscription%5Bplan%5D%5Bcolor%5D=&subscription%5Bplan%5D%5Bcharges%5D=365&subscription%5Bplan%5D%5Binstallments%5D=1&subscription%5Bplan%5D%5Binvoice_reminder%5D=&subscription%5Bplan%5D%5Bpayment_deadline_charges_interval%5D=1&subscription%5Bid%5D={SUBSCRIPTION_ID}&subscription%5Bcurrent_transaction%5D%5Bobject%5D=transaction&subscription%5Bcurrent_transaction%5D%5Bstatus%5D=waiting_payment&subscription%5Bcurrent_transaction%5D%5Brefuse_reason%5D=&subscription%5Bcurrent_transaction%5D%5Bstatus_reason%5D=acquirer&subscription%5Bcurrent_transaction%5D%5Bacquirer_response_code%5D=&subscription%5Bcurrent_transaction%5D%5Bacquirer_name%5D=pagarme&subscription%5Bcurrent_transaction%5D%5Bacquirer_id%5D=5f2da8e6d6f8614925b7cbc8&subscription%5Bcurrent_transaction%5D%5Bauthorization_code%5D=&subscription%5Bcurrent_transaction%5D%5Bsoft_descriptor%5D=&subscription%5Bcurrent_transaction%5D%5Btid%5D=9961453&subscription%5Bcurrent_transaction%5D%5Bnsu%5D=9961453&subscription%5Bcurrent_transaction%5D%5Bdate_created%5D=2020-10-07T06:50:45.092Z&subscription%5Bcurrent_transaction%5D%5Bdate_updated%5D=2020-10-07T06:50:45.452Z&subscription%5Bcurrent_transaction%5D%5Bamount%5D=5000&subscription%5Bcurrent_transaction%5D%5Bauthorized_amount%5D=5000&subscription%5Bcurrent_transaction%5D%5Bpaid_amount%5D=0&subscription%5Bcurrent_transaction%5D%5Brefunded_amount%5D=0&subscription%5Bcurrent_transaction%5D%5Binstallments%5D=1&subscription%5Bcurrent_transaction%5D%5Bid%5D={TRANSACTION_ID}&subscription%5Bcurrent_transaction%5D%5Bcost%5D=0&subscription%5Bcurrent_transaction%5D%5Bcard_holder_name%5D=&subscription%5Bcurrent_transaction%5D%5Bcard_last_digits%5D=&subscription%5Bcurrent_transaction%5D%5Bcard_first_digits%5D=&subscription%5Bcurrent_transaction%5D%5Bcard_brand%5D=&subscription%5Bcurrent_transaction%5D%5Bcard_pin_mode%5D=&subscription%5Bcurrent_transaction%5D%5Bcard_magstripe_fallback%5D=false&subscription%5Bcurrent_transaction%5D%5Bcvm_pin%5D=&subscription%5Bcurrent_transaction%5D%5Bpostback_url%5D=&subscription%5Bcurrent_transaction%5D%5Bpayment_method%5D=boleto&subscription%5Bcurrent_transaction%5D%5Bcapture_method%5D=ecommerce&subscription%5Bcurrent_transaction%5D%5Bantifraud_score%5D=&subscription%5Bcurrent_transaction%5D%5Bboleto_url%5D=https://api.pagar.me/1/boletos/test_ckfz199r40bar0mm5rnocm0x9&subscription%5Bcurrent_transaction%5D%5Bboleto_barcode%5D=23791.22928 60000.300370 41000.046908 2 84020000005000&subscription%5Bcurrent_transaction%5D%5Bboleto_expiration_date%5D=2020-10-08T06:50:45.078Z&subscription%5Bcurrent_transaction%5D%5Breferer%5D=&subscription%5Bcurrent_transaction%5D%5Bip%5D=&subscription%5Bcurrent_transaction%5D%5Bsubscription_id%5D={SUBSCRIPTION_ID}&subscription%5Bcurrent_transaction%5D%5Breference_key%5D=&subscription%5Bcurrent_transaction%5D%5Bdevice%5D=&subscription%5Bcurrent_transaction%5D%5Blocal_transaction_id%5D=&subscription%5Bcurrent_transaction%5D%5Blocal_time%5D=&subscription%5Bcurrent_transaction%5D%5Bfraud_covered%5D=false&subscription%5Bcurrent_transaction%5D%5Bfraud_reimbursed%5D=&subscription%5Bcurrent_transaction%5D%5Border_id%5D=&subscription%5Bcurrent_transaction%5D%5Brisk_level%5D=unknown&subscription%5Bcurrent_transaction%5D%5Breceipt_url%5D=&subscription%5Bcurrent_transaction%5D%5Bpayment%5D=&subscription%5Bcurrent_transaction%5D%5Baddition%5D=&subscription%5Bcurrent_transaction%5D%5Bdiscount%5D=&subscription%5Bcurrent_transaction%5D%5Bprivate_label%5D=&subscription%5Bpostback_url%5D=https://f01163e6ccc2c35f0b602134c8fd1b22.m.pipedream.net&subscription%5Bpayment_method%5D=boleto&subscription%5Bcard_brand%5D=&subscription%5Bcard_last_digits%5D=&subscription%5Bcurrent_period_start%5D=2020-10-07T06:50:45.075Z&subscription%5Bcurrent_period_end%5D=2020-10-08T06:50:45.078Z&subscription%5Bcharges%5D=1&subscription%5Bsoft_descriptor%5D=&subscription%5Bstatus%5D=paid&subscription%5Bdate_created%5D=2020-10-07T06:45:32.853Z&subscription%5Bdate_updated%5D=2020-10-07T06:50:45.508Z&subscription%5Bphone%5D%5Bobject%5D=phone&subscription%5Bphone%5D%5Bddi%5D=55&subscription%5Bphone%5D%5Bddd%5D=11&subscription%5Bphone%5D%5Bnumber%5D=48157549&subscription%5Bphone%5D%5Bid%5D=805178&subscription%5Baddress%5D%5Bobject%5D=address&subscription%5Baddress%5D%5Bstreet%5D=Rua Jacarandá&subscription%5Baddress%5D%5Bcomplementary%5D=&subscription%5Baddress%5D%5Bstreet_number%5D=123&subscription%5Baddress%5D%5Bneighborhood%5D=Gruta de Lourdes&subscription%5Baddress%5D%5Bcity%5D=Maceió&subscription%5Baddress%5D%5Bstate%5D=AL&subscription%5Baddress%5D%5Bzipcode%5D=57052575&subscription%5Baddress%5D%5Bcountry%5D=Brasil&subscription%5Baddress%5D%5Bid%5D=3475225&subscription%5Bcustomer%5D%5Bobject%5D=customer&subscription%5Bcustomer%5D%5Bid%5D=3858361&subscription%5Bcustomer%5D%5Bexternal_id%5D=&subscription%5Bcustomer%5D%5Btype%5D=&subscription%5Bcustomer%5D%5Bcountry%5D=&subscription%5Bcustomer%5D%5Bdocument_number%5D=17911211019&subscription%5Bcustomer%5D%5Bdocument_type%5D=cpf&subscription%5Bcustomer%5D%5Bname%5D=Zé&subscription%5Bcustomer%5D%5Bemail%5D=admin@example.com&subscription%5Bcustomer%5D%5Bphone_numbers%5D=&subscription%5Bcustomer%5D%5Bborn_at%5D=&subscription%5Bcustomer%5D%5Bbirthday%5D=&subscription%5Bcustomer%5D%5Bgender%5D=&subscription%5Bcustomer%5D%5Bdate_created%5D=2020-10-07T06:45:32.548Z&subscription%5Bcard%5D=&subscription%5Bmetadata%5D=&subscription%5Bsettled_charges%5D=&subscription%5Bmanage_token%5D=test_subscription_orEREv82rXhFxiLhvzmEHHTt5AgSva&subscription%5Bmanage_url%5D=https://pagar.me/customers/#/subscriptions/526141?token=test_subscription_orEREv82rXhFxiLhvzmEHHTt5'


@pytest.fixture
def subscription_signature(raw_post):
    hashed = hmac.new(settings.CHAVE_PAGARME_API_PRIVADA.encode(), raw_post.encode(), sha1)
    hex_signature = binascii.b2a_hex(hashed.digest())
    generated_signature = hex_signature.decode()
    return f'sha1={generated_signature}'


@pytest.fixture
def resp(client, plan, subscription, pagarme_payment, subscription_status_listener, raw_post, subscription_signature):
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': plan.slug}),
        raw_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=subscription_signature
    )


def test_status_code(resp):
    assert resp.status_code == 200


def test_notification_exists(resp):
    assert facade.find_subscription_by_id(SUBSCRIPTION_ID).notifications.exists()


def test_status_listener_executed(resp, subscription_status_listener):
    subscription = facade.find_subscription_by_id(str(SUBSCRIPTION_ID))
    subscription_status_listener.assert_called_once_with(subscription_id=subscription.id)


@pytest.fixture
def resp_tampered(client, plan, subscription, pagarme_payment, raw_post, subscription_signature):
    tampered_post = raw_post + 'r'
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': plan.slug}),
        tampered_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=subscription_signature
    )


def test_tampered_post(resp_tampered):
    assert resp_tampered.status_code == 400


# Testing not existing payment, it must be created

@pytest.fixture
def resp_no_payment(client, plan, subscription, subscription_status_listener, raw_post, subscription_signature):
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': plan.slug}),
        raw_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=subscription_signature
    )


def test_payment_creation(resp_no_payment):
    assert PagarmePayment.objects.exists()
