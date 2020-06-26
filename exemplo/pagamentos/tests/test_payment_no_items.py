import pytest
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmePayment, PagarmePaymentItem


def test_first_slug_exception(db):
    payment = baker.make(PagarmePayment)
    with pytest.raises(facade.PagarmePaymentItemDoesNotExist):
        payment.first_item_slug()
