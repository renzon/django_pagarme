from django.db import transaction as django_transaction
from pagarme import postback, transaction

from django_pagarme.models import (
    AUTHORIZED, PAID, PENDING_REFUND, PROCESSING, PagarmeNotification, PagarmePayment, PagarmeItemConfig, PaymentViolation,
    REFUNDED, REFUSED, WAITING_PAYMENT,
)

__all__ = ['get_payment_item',
           'capture',
           'PaymentViolation',
           'PROCESSING',
           'AUTHORIZED',
           'PAID',
           'REFUNDED',
           'PENDING_REFUND',
           'WAITING_PAYMENT',
           'REFUSED',
           ]


def get_payment_item(slug: str) -> PagarmeItemConfig:
    """
    Find PagarmeItemConfig with its PagarmeFormConfig on database
    :param slug:
    :return: PagarmeItemConfig
    """
    return PagarmeItemConfig.objects.filter(slug=slug).select_related('default_config').get()


def capture(token: str) -> PagarmePayment:
    pagarme_transaction = transaction.find_by_id(token)
    payment, all_payments_items = PagarmePayment.from_pagarme_transaction(pagarme_transaction)
    with django_transaction.atomic():
        payment.save()
        payment.items.set(all_payments_items)
        notification = PagarmeNotification(status=pagarme_transaction['status'], payment=payment)
        notification.save()

    transaction.capture(token, {'amount': payment.amount})
    return payment


def handle_notification(transaction_id: str, current_status: str, raw_body: str,
                        expected_signature: str) -> PagarmeNotification:
    if not postback.validate(expected_signature, raw_body):
        raise PaymentViolation('')
    payment_id = PagarmePayment.objects.values_list('id').get(transaction_id=transaction_id)[0]
    return _save_notification(payment_id, current_status)


_impossible_states = {
    PROCESSING: {PROCESSING},
    AUTHORIZED: {AUTHORIZED},
    PAID: {PAID, AUTHORIZED, WAITING_PAYMENT},
    REFUNDED: {REFUNDED, AUTHORIZED, PAID, WAITING_PAYMENT},
    PENDING_REFUND: {PENDING_REFUND, PAID, WAITING_PAYMENT, AUTHORIZED},
    WAITING_PAYMENT: {WAITING_PAYMENT},
    REFUSED: {REFUSED},
}


def _save_notification(payment_id, current_status):
    """
    Will save the notication depending on last status and current status
    raise Invalid Current Status in case current status is incompatible with last status
    :param payment_id:
    :param current_status:
    :return:
    """
    last_notification = PagarmeNotification.objects.filter(payment_id=payment_id).order_by('-creation').first()
    last_status = '' if last_notification is None else last_notification.status
    if current_status in _impossible_states.get(last_status, {}):
        raise InvalidNotificationStatusTransition(f'Invalid transition {last_status} -> {current_status}')
    return PagarmeNotification(status=current_status, payment_id=payment_id).save()


def find_payment(transaction_id: str):
    transaction_id = str(transaction_id)
    return PagarmePayment.objects.get(transaction_id=transaction_id)


class InvalidNotificationStatusTransition(Exception):
    pass
