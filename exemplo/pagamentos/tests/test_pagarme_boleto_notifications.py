import binascii
import hmac
from _sha1 import sha1

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmeFormConfig, PagarmeItemConfig, PagarmePayment


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
def pagarme_payment(payment_item):
    payment = baker.make(PagarmePayment, transaction_id=str(TRANSACTION_ID))
    payment.items.set([payment_item])
    payment.save()
    return payment


@pytest.fixture
def payment_status_listener(mocker):
    mock = mocker.Mock()
    facade.add_payment_status_changed(mock)
    yield mock
    facade._payment_status_changed_listeners.pop()


TRANSACTION_ID = 7789955


@pytest.fixture
def raw_post(payment_item: PagarmeItemConfig):
    # noqa
    post = (
        f'id={TRANSACTION_ID}&fingerprint=f04f4a3655e5acb3358ccca013afa6b49cc2cb58&event=transaction_status_changed&old_status=processing&desired_status=authorized&current_status=authorized&object=transaction&transaction%5Bobject%5D=transaction&transaction%5Bstatus%5D=authorized&transaction%5Brefuse_reason%5D=&transaction%5Bstatus_reason%5D=acquirer&transaction%5Bacquirer_response_code%5D=&transaction%5Bacquirer_name%5D=pagarme&transaction%5Bacquirer_id%5D=5cdec7071458b442125d940b&transaction%5Bauthorization_code%5D=&transaction%5Bsoft_descriptor%5D=&'
        f'transaction%5Btid%5D={TRANSACTION_ID}&transaction%5Bnsu%5D={TRANSACTION_ID}&transaction%5Bdate_created%5D=2020-06-24T17%3A21%3A14.296Z&transaction%5Bdate_updated%5D=2020-06-24T17%3A21%3A14.464Z&'
        f'transaction%5Bamount%5D=39700&transaction%5Bauthorized_amount%5D={payment_item.price}&transaction%5Bpaid_amount%5D=0&transaction%5Brefunded_amount%5D=0&transaction%5Binstallments%5D=1&transaction%5Bid%5D={TRANSACTION_ID}&transaction%5Bcost%5D=0&transaction%5Bcard_holder_name%5D=&transaction%5Bcard_last_digits%5D=&transaction%5Bcard_first_digits%5D=&transaction%5Bcard_brand%5D=&transaction%5Bcard_pin_mode%5D=&transaction%5Bcard_magstripe_fallback%5D=false&transaction%5Bcvm_pin%5D=false&transaction%5Bpostback_url%5D=https%3A%2F%2Fa203b199d7c5.ngrok.io%2Fcheckout%2Fnotification%2Fpytools&transaction%5Bpayment_method%5D=boleto&transaction%5Bcapture_method%5D=ecommerce&transaction%5Bantifraud_score%5D=&transaction%5Bboleto_url%5D=&transaction%5Bboleto_barcode%5D=&transaction%5Bboleto_expiration_date%5D=2020-06-26T03%3A00%3A00.000Z&transaction%5Breferer%5D=encryption_key&transaction%5Bip%5D=177.62.111.138&transaction%5Bsubscription_id%5D=&transaction%5Bphone%5D=&transaction%5Baddress%5D=&transaction%5Bcustomer%5D%5Bobject%5D=customer&transaction%5Bcustomer%5D%5Bid%5D=3336966&transaction%5Bcustomer%5D%5Bexternal_id%5D=renzo%40python.pro.br&transaction%5Bcustomer%5D%5Btype%5D=individual&transaction%5Bcustomer%5D%5Bcountry%5D=br&transaction%5Bcustomer%5D%5Bdocument_number%5D=&transaction%5Bcustomer%5D%5Bdocument_type%5D=cpf&transaction%5Bcustomer%5D%5Bname%5D=Renzo%20Teste%20Checkout&transaction%5Bcustomer%5D%5Bemail%5D=renzo%40python.pro.br&transaction%5Bcustomer%5D%5Bphone_numbers%5D%5B0%5D=%2B5599999999888&transaction%5Bcustomer%5D%5Bborn_at%5D=&transaction%5Bcustomer%5D%5Bbirthday%5D=&transaction%5Bcustomer%5D%5Bgender%5D=&transaction%5Bcustomer%5D%5Bdate_created%5D=2020-06-24T17%3A21%3A14.231Z&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bobject%5D=document&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bid%5D=doc_ckbtmjmrp040b8e6d8n2h1tkc&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Btype%5D=cpf&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bnumber%5D=29770166863&transaction%5Bbilling%5D%5Bobject%5D=billing&transaction%5Bbilling%5D%5Bid%5D=1418839&transaction%5Bbilling%5D%5Bname%5D=Renzo%20Teste%20Checkout&transaction%5Bbilling%5D%5Baddress%5D%5Bobject%5D=address&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet%5D=Rua%20Curacao&transaction%5Bbilling%5D%5Baddress%5D%5Bcomplementary%5D=Sem%20complemento&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet_number%5D=494&transaction%5Bbilling%5D%5Baddress%5D%5Bneighborhood%5D=Cidade%20Vista%20Verde&transaction%5Bbilling%5D%5Baddress%5D%5Bcity%5D=S%C3%A3o%20Jos%C3%A9%20dos%20Campos&transaction%5Bbilling%5D%5Baddress%5D%5Bstate%5D=SP&transaction%5Bbilling%5D%5Baddress%5D%5Bzipcode%5D=12223750&transaction%5Bbilling%5D%5Baddress%5D%5Bcountry%5D=br&transaction%5Bbilling%5D%5Baddress%5D%5Bid%5D=3099539&transaction%5Bshipping%5D=&'
        f'transaction%5Bitems%5D%5B0%5D%5Bobject%5D=item&transaction%5Bitems%5D%5B0%5D%5Bid%5D={payment_item.slug}&transaction%5Bitems%5D%5B0%5D%5Btitle%5D=Curso%20Pytools&'
        f'transaction%5Bitems%5D%5B0%5D%5Bunit_price%5D={payment_item.price}&transaction%5Bitems%5D%5B0%5D%5Bquantity%5D=1&transaction%5Bitems%5D%5B0%5D%5Bcategory%5D=&transaction%5Bitems%5D%5B0%5D%5Btangible%5D=false&transaction%5Bitems%5D%5B0%5D%5Bvenue%5D=&transaction%5Bitems%5D%5B0%5D%5Bdate%5D=&transaction%5Bcard%5D=&transaction%5Bsplit_rules%5D=&transaction%5Breference_key%5D=&transaction%5Bdevice%5D=&transaction%5Blocal_transaction_id%5D=&transaction%5Blocal_time%5D=&transaction%5Bfraud_covered%5D=false&transaction%5Bfraud_reimbursed%5D=&transaction%5Border_id%5D=&transaction%5Brisk_level%5D=unknown&transaction%5Breceipt_url%5D=&transaction%5Bpayment%5D=&transaction%5Baddition%5D=&transaction%5Bdiscount%5D=&transaction%5Bprivate_label%5D='
    )


    return post


@pytest.fixture
def transaction_signature(raw_post):
    hashed = hmac.new(settings.CHAVE_PAGARME_API_PRIVADA.encode(), raw_post.encode(), sha1)
    hex_signature = binascii.b2a_hex(hashed.digest())
    generated_signature = hex_signature.decode()
    return f'sha1={generated_signature}'


@pytest.fixture
def resp(client, pagarme_payment, payment_item, payment_status_listener, raw_post, transaction_signature):
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': payment_item.slug}),
        raw_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=transaction_signature
    )


def test_status_code(resp):
    assert resp.status_code == 200


def test_notification_exists(resp):
    assert facade.find_payment_by_transaction(TRANSACTION_ID).notifications.exists()


def test_status_listener_executed(resp, payment_status_listener):
    payment = facade.find_payment_by_transaction(str(TRANSACTION_ID))
    payment_status_listener.assert_called_once_with(payment_id=payment.id)


@pytest.fixture
def resp_tampered(client, pagarme_payment, payment_item, raw_post, transaction_signature):
    tampered_post = raw_post + 'r'
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': payment_item.slug}),
        tampered_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=transaction_signature
    )


def test_tampered_post(resp_tampered):
    assert resp_tampered.status_code == 400


# Testing not existing payment, it must be created

@pytest.fixture
def resp_no_payment(client, payment_item, payment_status_listener, raw_post, transaction_signature):
    return client.generic(
        'POST',
        reverse('django_pagarme:notification', kwargs={'slug': payment_item.slug}),
        raw_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=transaction_signature
    )


def test_payment_creation(resp_no_payment):
    assert PagarmePayment.objects.exists()
