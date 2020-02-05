from django.db import transaction as django_transaction
from pagarme import transaction

from django_pagarme.models import PagarmePayment, PaymentItem, PaymentViolation

__all__ = ['get_payment_item', 'capture', 'PaymentViolation']


def get_payment_item(slug: str) -> PaymentItem:
    """
    Find PaymentItem with its PaymentConfig on database
    :param slug:
    :return: PaymentItem
    """
    return PaymentItem.objects.filter(slug=slug).select_related('default_config').get()


def capture(token: str) -> PagarmePayment:
    pagarme_transaction = transaction.find_by_id(token)
    payment, all_payments_items = PagarmePayment.from_pagarme_transaction(pagarme_transaction)
    with django_transaction.atomic():
        payment.save()
        payment.items.set(all_payments_items)
    transaction.capture(token, {'amount': payment.amount})
    return payment
