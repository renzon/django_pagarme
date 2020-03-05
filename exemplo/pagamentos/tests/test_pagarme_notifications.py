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
def resp(client, pagarme_payment):
    return client.generic(
        'POST',
        reverse('django_pagarme:notification'),
        RAW_POST.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=TRANSACTION_SIGNATURE
    )


def test_status_code(resp):
    assert resp.status_code == 200


def test_notification_exists(resp):
    assert facade.find_payment(TRANSACTION_ID).notifications.exists()


@pytest.fixture
def resp_tampered(client, pagarme_payment):
    tampered_post = RAW_POST + 'r'
    return client.generic(
        'POST',
        reverse('django_pagarme:notification'),
        tampered_post.encode('utf8'),
        content_type='application/x-www-form-urlencoded',
        HTTP_X_HUB_SIGNATURE=TRANSACTION_SIGNATURE
    )


def test_tampered_post(resp_tampered):
    assert resp_tampered.status_code == 400


TRANSACTION_ID = 7789955
# noqa
RAW_POST = f'''id={TRANSACTION_ID}&fingerprint=b84ca60027a959048f165da94e8be3749dff1792&event=transaction_status_changed&old_status={facade.PROCESSING}&desired_status=authorized&current_status={facade.AUTHORIZED}&object=transaction&transaction%5Bobject%5D=transaction&transaction%5Bstatus%5D=authorized&transaction%5Brefuse_reason%5D=&transaction%5Bstatus_reason%5D=antifraud&transaction%5Bacquirer_response_code%5D=0000&transaction%5Bacquirer_name%5D=pagarme&transaction%5Bacquirer_id%5D=5cdec7071458b442125d940b&transaction%5Bauthorization_code%5D=269217&transaction%5Bsoft_descriptor%5D=&transaction%5Btid%5D={TRANSACTION_ID}&transaction%5Bnsu%5D={TRANSACTION_ID}&transaction%5Bdate_created%5D=2020-02-11T01%3A51%3A12.385Z&transaction%5Bdate_updated%5D=2020-02-11T01%3A51%3A12.792Z&transaction%5Bamount%5D=39700&transaction%5Bauthorized_amount%5D=39700&transaction%5Bpaid_amount%5D=0&transaction%5Brefunded_amount%5D=0&transaction%5Binstallments%5D=1&transaction%5Bid%5D={TRANSACTION_ID}&transaction%5Bcost%5D=70&transaction%5Bcard_holder_name%5D=Ngrok%20Card&transaction%5Bcard_last_digits%5D=1111&transaction%5Bcard_first_digits%5D=411111&transaction%5Bcard_brand%5D=visa&transaction%5Bcard_pin_mode%5D=&transaction%5Bcard_magstripe_fallback%5D=false&transaction%5Bcvm_pin%5D=false&transaction%5Bpostback_url%5D=http%3A%2F%2Fa2ffad64.ngrok.io%2Fdjango_pagarme%2Fnotification&transaction%5Bpayment_method%5D=credit_card&transaction%5Bcapture_method%5D=ecommerce&transaction%5Bantifraud_score%5D=&transaction%5Bboleto_url%5D=&transaction%5Bboleto_barcode%5D=&transaction%5Bboleto_expiration_date%5D=&transaction%5Breferer%5D=encryption_key&transaction%5Bip%5D=177.62.218.2&transaction%5Bsubscription_id%5D=&transaction%5Bphone%5D=&transaction%5Baddress%5D=&transaction%5Bcustomer%5D%5Bobject%5D=customer&transaction%5Bcustomer%5D%5Bid%5D=2663118&transaction%5Bcustomer%5D%5Bexternal_id%5D=ngrok%40email.com&transaction%5Bcustomer%5D%5Btype%5D=individual&transaction%5Bcustomer%5D%5Bcountry%5D=br&transaction%5Bcustomer%5D%5Bdocument_number%5D=&transaction%5Bcustomer%5D%5Bdocument_type%5D=cpf&transaction%5Bcustomer%5D%5Bname%5D=Ngrok&transaction%5Bcustomer%5D%5Bemail%5D=ngrok%40email.com&transaction%5Bcustomer%5D%5Bphone_numbers%5D%5B0%5D=%2B5512977777777&transaction%5Bcustomer%5D%5Bborn_at%5D=&transaction%5Bcustomer%5D%5Bbirthday%5D=&transaction%5Bcustomer%5D%5Bgender%5D=&transaction%5Bcustomer%5D%5Bdate_created%5D=2020-02-11T01%3A51%3A12.296Z&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bobject%5D=document&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bid%5D=doc_ck6h8bge103z6336fjvo5otkl&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Btype%5D=cpf&transaction%5Bcustomer%5D%5Bdocuments%5D%5B0%5D%5Bnumber%5D=29770166863&transaction%5Bbilling%5D%5Bobject%5D=billing&transaction%5Bbilling%5D%5Bid%5D=1149582&transaction%5Bbilling%5D%5Bname%5D=Ngrok&transaction%5Bbilling%5D%5Baddress%5D%5Bobject%5D=address&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet%5D=Rua%20Buenos%20Aires&transaction%5Bbilling%5D%5Baddress%5D%5Bcomplementary%5D=Sem%20complemento&transaction%5Bbilling%5D%5Baddress%5D%5Bstreet_number%5D=4&transaction%5Bbilling%5D%5Baddress%5D%5Bneighborhood%5D=Cidade%20Vista%20Verde&transaction%5Bbilling%5D%5Baddress%5D%5Bcity%5D=S%C3%A3o%20Jos%C3%A9%20dos%20Campos&transaction%5Bbilling%5D%5Baddress%5D%5Bstate%5D=SP&transaction%5Bbilling%5D%5Baddress%5D%5Bzipcode%5D=12223730&transaction%5Bbilling%5D%5Baddress%5D%5Bcountry%5D=br&transaction%5Bbilling%5D%5Baddress%5D%5Bid%5D=2602652&transaction%5Bshipping%5D=&transaction%5Bitems%5D%5B0%5D%5Bobject%5D=item&transaction%5Bitems%5D%5B0%5D%5Bid%5D=pytools&transaction%5Bitems%5D%5B0%5D%5Btitle%5D=Pytools&transaction%5Bitems%5D%5B0%5D%5Bunit_price%5D=39700&transaction%5Bitems%5D%5B0%5D%5Bquantity%5D=1&transaction%5Bitems%5D%5B0%5D%5Bcategory%5D=&transaction%5Bitems%5D%5B0%5D%5Btangible%5D=false&transaction%5Bitems%5D%5B0%5D%5Bvenue%5D=&transaction%5Bitems%5D%5B0%5D%5Bdate%5D=&transaction%5Bcard%5D%5Bobject%5D=card&transaction%5Bcard%5D%5Bid%5D=card_ck6h8bgfj03z7336fru9krd8z&transaction%5Bcard%5D%5Bdate_created%5D=2020-02-11T01%3A51%3A12.368Z&transaction%5Bcard%5D%5Bdate_updated%5D=2020-02-11T01%3A51%3A12.869Z&transaction%5Bcard%5D%5Bbrand%5D=visa&transaction%5Bcard%5D%5Bholder_name%5D=Ngrok%20Card&transaction%5Bcard%5D%5Bfirst_digits%5D=411111&transaction%5Bcard%5D%5Blast_digits%5D=1111&transaction%5Bcard%5D%5Bcountry%5D=UNITED%20STATES&transaction%5Bcard%5D%5Bfingerprint%5D=cj5bw4cio00000j23jx5l60cq&transaction%5Bcard%5D%5Bvalid%5D=true&transaction%5Bcard%5D%5Bexpiration_date%5D=1228&transaction%5Bsplit_rules%5D=&transaction%5Breference_key%5D=&transaction%5Bdevice%5D=&transaction%5Blocal_transaction_id%5D=&transaction%5Blocal_time%5D=&transaction%5Bfraud_covered%5D=false&transaction%5Bfraud_reimbursed%5D=&transaction%5Border_id%5D=&transaction%5Brisk_level%5D=very_low&transaction%5Breceipt_url%5D=&transaction%5Bpayment%5D=&transaction%5Baddition%5D=&transaction%5Bdiscount%5D=&transaction%5Bprivate_label%5D='''
hashed = hmac.new(settings.CHAVE_PAGARME_API_PRIVADA.encode(), RAW_POST.encode(), sha1)
hex_signature = binascii.b2a_hex(hashed.digest())
generated_signature = hex_signature.decode()

TRANSACTION_SIGNATURE = f'sha1={generated_signature}'
