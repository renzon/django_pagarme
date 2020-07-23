import pytest
from model_bakery import baker

from django_pagarme import facade
from django_pagarme.models import PagarmeNotification, PagarmePayment

TRANSACTION_ID = '1234'


@pytest.fixture
def pagarme_payment(db):
    payment = baker.make(PagarmePayment, transaction_id=str(TRANSACTION_ID))
    return payment


@pytest.mark.parametrize(
    'status',
    [
        facade.PAID,
        facade.PENDING_REFUND,
        facade.REFUNDED,
        facade.REFUSED,
        facade.WAITING_PAYMENT,
        facade.PROCESSING,
    ]
)
def test_repeated_notification_not_saved(status, pagarme_payment):
    PagarmeNotification(status=status, payment=pagarme_payment).save()
    with pytest.raises(facade.InvalidNotificationStatusTransition):
        facade._save_notification(pagarme_payment.id, status)
    assert PagarmePayment.objects.count() == 1


@pytest.mark.parametrize(
    'status_from, status_to',
    [
        (facade.PAID, facade.AUTHORIZED),
        (facade.PAID, facade.WAITING_PAYMENT),
        (facade.PENDING_REFUND, facade.PAID),
        (facade.PENDING_REFUND, facade.WAITING_PAYMENT),
        (facade.PENDING_REFUND, facade.AUTHORIZED),
        (facade.REFUNDED, facade.PAID),
        (facade.REFUNDED, facade.WAITING_PAYMENT),
        (facade.REFUNDED, facade.AUTHORIZED),
        (facade.REFUNDED, facade.AUTHORIZED),
    ]
)
def test_invalid_transition(status_from, status_to, pagarme_payment):
    PagarmeNotification(status=status_from, payment=pagarme_payment).save()
    with pytest.raises(facade.InvalidNotificationStatusTransition):
        facade._save_notification(pagarme_payment.id, status_to)
    assert PagarmePayment.objects.count() == 1
