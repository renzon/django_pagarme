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
        payments_methods='credit_card'
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
        f'id={TRANSACTION_ID}&fingerprint=b84ca60027a959048f165da94e8be3749dff1792&event=transaction_status_changed&old_status={facade.AUTHORIZED}&desired_status=authorized&current_status={facade.AUTHORIZED}&object=transaction&transaction%5Bobject%5D=transaction&transaction%5Bstatus%5D=authorized&transaction%5Brefuse_reason%5D=&transaction%5Bstatus_reason%5D=antifraud&transaction%5Bacquirer_response_code%5D=0000&transaction%5Bacquirer_name%5D=pagarme&transaction%5Bacquirer_id%5D=5cdec7071458b442125d940b&transaction%5Bauthorization_code%5D=269217&transaction%5Bsoft_descriptor%5D=&transaction%5Btid%5D={TRANSACTION_ID}&transaction%5Bnsu%5D={TRANSACTION_ID}&transaction%5Bdate_created%5D=2020-02-11T01%3A51%3A12.385Z&transaction%5Bdate_updated%5D=2020-02-11T01%3A51%3A12.792Z&'
        f'transaction%5Bamount%5D=39700&transaction%5Bauthorized_amount%5D={payment_item.price}&transaction%5Bpaid_amount%5D=0&transaction%5Brefunded_amount%5D=0&transaction%5Binstallments%5D=1&transaction%5Bid%5D={TRANSACTION_ID}&transaction%5Bcost%5D=70&transaction%5Bcard_holder_name%5D=Ngrok%20Card&transaction%5Bcard_last_digits%5D=1111&transaction%5Bcard_first_digits%5D=411111&transaction%5Bcard_brand%5D=visa&transaction%5Bcard_pin_mode%5D=&transaction%5Bcard_magstripe_fallback%5D=false&transaction%5Bcvm_pin%5D=false&transaction%5Bpostback_url%5D=http%3A%2F%2Fa2ffad64.ngrok.io%2Fdjango_pagarme%2Fnotification&transaction%5Bpayment_method%5D=credit_card&transaction%5Bcapture_method%5D=ecommerce&transaction%5Bantifraud_score%5D=&transaction%5Bboleto_url%5D=&transaction%5Bboleto_barcode%5D=&transaction%5Bboleto_expiration_date%5D=&transaction%5Breferer%5D=encryption_key&transaction%5Bip%5D=177.62.218.2&transaction%5Bsubscription_id%5D=&transaction%5Bphone%5D=&transaction%5Baddress%5D=&transaction%5Bcustomer%5D%5Bobject%5D=customer&transaction%5Bcustomer%5D%5Bid%5D=2663118&transaction%5Bcustomer%5D%5Bexternal_id%5D=ngrok%40email.com&transaction%5Bcustomer%5D%5Btype%5D=individual&transaction%5Bcustomer%5D%5Bcountry%5D=br&transaction%5Bcustomer%5D%5Bdocument_number%5D=&transaction%5Bcustomer%5D%5Bdocument_type%5D=cpf&transaction%5Bcustomer%5D%5Bname%5D=Ngrok&transaction%5Bcustomer%5D%5Bemail%5D=ngrok%40email.com&transaction%5Bcustomer%5D%5Bphone_numbers%5D%5B0%5D=%2B5512977777777&transaction%5Bcustomer%5D%5Bborn_at%5D=&transaction%5Bcustomer%5D%5Bbirthday%5D=&transaction%5Bcustomer%5D%5Bgender%5D=&transaction%5Bcustomer%5D%5Bdate_created%5D=2020-02-11T01%3A51%3A12.296Z&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bobject%5D=document&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bid%5D=doc_ck6h8bge103z6336fjvo5otkl&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Btype%5D=cpf&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bnumber%5D=29770166863&transaction%5Bbilling%5D%5Bobject%5D=billing&transaction%5Bbilling%5D%5Bid%5D=1149582&transaction%5Bbilling%5D%5Bname%5D=Ngrok&transaction%5Bbilling%5D%5Baddress%5D%5Bobject%5D=address&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet%5D=Rua%20Buenos%20Aires&transaction%5Bbilling%5D%5Baddress%5D%5Bcomplementary%5D=Sem%20complemento&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet_number%5D=4&transaction%5Bbilling%5D%5Baddress%5D%5Bneighborhood%5D=Cidade%20Vista%20Verde&transaction%5Bbilling%5D%5Baddress%5D%5Bcity%5D=S%C3%A3o%20Jos%C3%A9%20dos%20Campos&transaction%5Bbilling%5D%5Baddress%5D%5Bstate%5D=SP&transaction%5Bbilling%5D%5Baddress%5D%5Bzipcode%5D=12223730&transaction%5Bbilling%5D%5Baddress%5D%5Bcountry%5D=br&transaction%5Bbilling%5D%5Baddress%5D%5Bid%5D=2602652&transaction%5Bshipping%5D=&transaction%5Bitems%5D%5B0%5D%5Bobject%5D=item&'
        f'transaction%5Bitems%5D%5B0%5D%5Bid%5D={payment_item.slug}&transaction%5Bitems%5D%5B0%5D%5Btitle%5D=Pytools&'
        f'transaction%5Bitems%5D%5B0%5D%5Bunit_price%5D={payment_item.price}&transaction%5Bitems%5D%5B0%5D%5Bquantity%5D=1&transaction%5Bitems%5D%5B0%5D%5Bcategory%5D=&transaction%5Bitems%5D%5B0%5D%5Btangible%5D=false&transaction%5Bitems%5D%5B0%5D%5Bvenue%5D=&transaction%5Bitems%5D%5B0%5D%5Bdate%5D=&transaction%5Bcard%5D%5Bobject%5D=card&transaction%5Bcard%5D%5Bid%5D=card_ck6h8bgfj03z7336fru9krd8z&transaction%5Bcard%5D%5Bdate_created%5D=2020-02-11T01%3A51%3A12.368Z&transaction%5Bcard%5D%5Bdate_updated%5D=2020-02-11T01%3A51%3A12.869Z&transaction%5Bcard%5D%5Bbrand%5D=visa&transaction%5Bcard%5D%5Bholder_name%5D=Ngrok%20Card&transaction%5Bcard%5D%5Bfirst_digits%5D=411111&transaction%5Bcard%5D%5Blast_digits%5D=1111&transaction%5Bcard%5D%5Bcountry%5D=UNITED%20STATES&transaction%5Bcard%5D%5Bfingerprint%5D=cj5bw4cio00000j23jx5l60cq&transaction%5Bcard%5D%5Bvalid%5D=true&transaction%5Bcard%5D%5Bexpiration_date%5D=1228&transaction%5Bsplit_rules%5D=&transaction%5Breference_key%5D=&transaction%5Bdevice%5D=&transaction%5Blocal_transaction_id%5D=&transaction%5Blocal_time%5D=&transaction%5Bfraud_covered%5D=false&transaction%5Bfraud_reimbursed%5D=&transaction%5Border_id%5D=&transaction%5Brisk_level%5D=very_low&transaction%5Breceipt_url%5D=&transaction%5Bpayment%5D=&transaction%5Baddition%5D=&transaction%5Bdiscount%5D=&transaction%5Bprivate_label%5D='
    )
    return post


def _transaction_signature(raw_post):
    hashed = hmac.new(settings.CHAVE_PAGARME_API_PRIVADA.encode(), raw_post.encode(), sha1)
    hex_signature = binascii.b2a_hex(hashed.digest())
    generated_signature = hex_signature.decode()
    return f'sha1={generated_signature}'


@pytest.fixture
def transaction_signature(raw_post):
    return _transaction_signature(raw_post)


@pytest.fixture
def resp(client, pagarme_payment, payment_item, payment_status_listener, raw_post, transaction_signature):
    return _make_signed_post(client, payment_item, raw_post, transaction_signature)


def _make_signed_post(client, payment_item, raw_post, transaction_signature):
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


# Test refused payment

@pytest.fixture
def raw_refused_post(payment_item: PagarmeItemConfig, user):
    # noqa
    post = (
        f'id={TRANSACTION_ID}&fingerprint=d15498de0c818b8d083b0c4ebd3385d19e280d1e&event=transaction_status_changed&old_status=processing&desired_status=authorized&current_status=refused&object=transaction&transaction%5Bobject%5D=transaction&transaction%5Bstatus%5D=refused&transaction%5Brefuse_reason%5D=acquirer&transaction%5Bstatus_reason%5D=acquirer&transaction%5Bacquirer_response_code%5D=1009&transaction%5Bacquirer_name%5D=pagarme&transaction%5Bacquirer_id%5D=5cdec7071458b442125d940b&transaction%5Bauthorization_code%5D=&transaction%5Bsoft_descriptor%5D=&transaction%5Btid%5D=9212497&transaction%5Bnsu%5D=9212497&transaction%5Bdate_created%5D=2020-07-14T14%3A00%3A43.007Z&transaction%5Bdate_updated%5D=2020-07-14T14%3A00%3A43.570Z&transaction%5Bamount%5D=39700&transaction%5B'
        f'authorized_amount%5D=0&transaction%5Bpaid_amount%5D=0&transaction%5Brefunded_amount%5D=0&transaction%5Binstallments%5D=1&transaction%5Bid%5D=9212497&transaction%5Bcost%5D=0&transaction%5Bcard_holder_name%5D=Cartao%20Recusado&transaction%5Bcard_last_digits%5D=1111&transaction%5Bcard_first_digits%5D=411111&transaction%5Bcard_brand%5D=visa&transaction%5Bcard_pin_mode%5D=&transaction%5Bcard_magstripe_fallback%5D=false&transaction%5Bcvm_pin%5D=false&transaction%5Bpostback_url%5D=https%3A%2F%2F1805e365912e.ngrok.io%2Fcheckout%2Fnotification%2Fpytools&transaction%5Bpayment_method%5D=credit_card&transaction%5Bcapture_method%5D=ecommerce&transaction%5Bantifraud_score%5D=&transaction%5Bboleto_url%5D=&transaction%5Bboleto_barcode%5D=&transaction%5Bboleto_expiration_date%5D=&transaction%5Breferer%5D=encryption_key&transaction%5Bip%5D=177.62.131.125&transaction%5Bsubscription_id%5D=&transaction%5Bphone%5D=&transaction%5Baddress%5D=&'
        f'transaction%5Bcustomer%5D%5Bobject%5D=customer&'
        f'transaction%5Bcustomer%5D%5Bid%5D=3426732&'
        f'transaction%5Bcustomer%5D%5Bexternal_id%5D={user.id}&'
        f'transaction%5Bcustomer%5D%5Btype%5D=individual&'
        f'transaction%5Bcustomer%5D%5Bcountry%5D=br&'
        f'transaction%5Bcustomer%5D%5Bdocument_number%5D=&'
        f'transaction%5Bcustomer%5D%5Bdocument_type%5D=cpf&'
        f'transaction%5Bcustomer%5D%5Bname%5D=Renzo%20Teste%20Checkout&'
        f'transaction%5Bcustomer%5D%5Bemail%5D=renzo%40python.pro.br&'
        f'transaction%5Bcustomer%5D%5Bphone_numbers%5D%5B0%5D=%2B5512999999999&'
        f'transaction%5Bcustomer%5D%5Bborn_at%5D=&'
        f'transaction%5Bcustomer%5D%5Bbirthday%5D=&'
        f'transaction%5Bcustomer%5D%5Bgender%5D=&'
        f'transaction%5Bcustomer%5D%5Bdate_created%5D=2020-07-14T14%3A00%3A42.934Z&'
        f'transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bobject%5D=document&'
        f'transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bid%5D=doc_ckcm06sp1005lzg6de303uiz3&'
        f'transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Btype%5D=cpf&'
        f'transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bnumber%5D=49998707030&'
        f'transaction%5Bbilling%5D%5Bobject%5D=billing&'
        f'transaction%5Bbilling%5D%5Bid%5D=1461139&'
        f'transaction%5Bbilling%5D%5Bname%5D=Renzo%20Teste%20Checkout&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bobject%5D=address&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bstreet%5D=Rua%20Buenos%20Aires&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bcomplementary%5D=&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bstreet_number%5D=4&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bneighborhood%5D=Cidade%20Vista%20Verde&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bcity%5D=S%C3%A3o%20Jos%C3%A9%20dos%20Campos&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bstate%5D=SP&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bzipcode%5D=12223730&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bcountry%5D=br&'
        f'transaction%5Bbilling%5D%5Baddress%5D%5Bid%5D=3188083&'
        f'transaction%5Bshipping%5D=&'
        f'transaction%5Bitems%5D%5B0%5D%5Bobject%5D=item&'
        f'transaction%5Bitems%5D%5B0%5D%5Bid%5D={payment_item.slug}&'
        f'transaction%5Bitems%5D%5B0%5D%5Btitle%5D=Curso%20Pytools&'
        f'transaction%5Bitems%5D%5B0%5D%5Bunit_price%5D={payment_item.price}&'
        f'transaction%5Bitems%5D%5B0%5D%5Bquantity%5D=1&'
        f'transaction%5Bitems%5D%5B0%5D%5Bcategory%5D=&'
        f'transaction%5Bitems%5D%5B0%5D%5Btangible%5D=false&'
        f'transaction%5Bitems%5D%5B0%5D%5Bvenue%5D=&'
        f'transaction%5Bitems%5D%5B0%5D%5Bdate%5D=&'
        f'transaction%5Bcard%5D%5Bobject%5D=card&'
        f'transaction%5Bcard%5D%5Bid%5D=card_ckcm06sq9005mzg6dz7bv96wv&transaction%5Bcard%5D%5Bdate_created%5D=2020-07-14T14%3A00%3A42.993Z&transaction%5Bcard%5D%5Bdate_updated%5D=2020-07-14T14%3A00%3A43.636Z&transaction%5Bcard%5D%5Bbrand%5D=visa&transaction%5Bcard%5D%5Bholder_name%5D=Cartao%20Recusado&transaction%5Bcard%5D%5Bfirst_digits%5D=411111&transaction%5Bcard%5D%5Blast_digits%5D=1111&transaction%5Bcard%5D%5Bcountry%5D=UNITED%20STATES&transaction%5Bcard%5D%5Bfingerprint%5D=cj5bw4cio00000j23jx5l60cq&transaction%5Bcard%5D%5Bvalid%5D=false&transaction%5Bcard%5D%5Bexpiration_date%5D=1228&transaction%5Bsplit_rules%5D=&transaction%5Breference_key%5D=&transaction%5Bdevice%5D=&transaction%5Blocal_transaction_id%5D=&transaction%5Blocal_time%5D=&transaction%5Bfraud_covered%5D=false&transaction%5Bfraud_reimbursed%5D=&transaction%5Border_id%5D=&transaction%5Brisk_level%5D=unknown&transaction%5Breceipt_url%5D=&transaction%5Bpayment%5D=&transaction%5Baddition%5D=&transaction%5Bdiscount%5D=&transaction%5Bprivate_label%5D='
    )
    return post


@pytest.fixture
def refused_transaction_signature(raw_refused_post):
    return _transaction_signature(raw_refused_post)


@pytest.fixture
def user(django_user_model):
    return baker.make(django_user_model)


@pytest.fixture
def refused_resp(client, payment_item, payment_status_listener, raw_refused_post, refused_transaction_signature, user):
    # this user is not logged, will be used as return of factory function
    factory_user = user

    def factory(pagarme_transaction):
        return factory_user

    facade.set_user_factory(factory)
    yield _make_signed_post(client, payment_item, raw_refused_post, refused_transaction_signature)
    # returning factory to original function
    facade._user_factory = facade._default_factory


def test_refused_payment_creation(refused_resp):
    assert PagarmePayment.objects.exists()


def test_refused_payment_status(refused_resp):
    assert PagarmePayment.objects.first().status() == facade.REFUSED


def test_refused_payment_item_connections(refused_resp, payment_item):
    assert PagarmePayment.objects.first().first_item_slug() == payment_item.slug


def test_refused_payment_user_connection(refused_resp, user):
    assert PagarmePayment.objects.first().user_id == user.id


def test_refused_payment_user_profile_exists(refused_resp, user):
    assert facade.get_user_payment_profile(user) is not None
