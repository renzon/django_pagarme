from django_pagarme.models import PaymentItem

__all__ = ['get_payment_item']


def get_payment_item(slug: str) -> PaymentItem:
    """
    Find PaymentItem with its PaymentConfig on database
    :param slug:
    :return: PaymentItem
    """
    return PaymentItem.objects.filter(slug=slug).select_related('default_config').get()
