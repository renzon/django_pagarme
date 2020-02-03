from django_pagarme.models import Sellable

__all__ = ['get_sellable']


def get_sellable(slug: str) -> Sellable:
    """
    Find Sellable with its SellableOption on database
    :param slug:
    :return: Sellable
    """
    return Sellable.objects.filter(slug=slug).select_related('default_option').get()
