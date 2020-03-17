from typing import Callable, List

from django.contrib.auth import get_user_model
from django.db import transaction as django_transaction
from pagarme import postback, transaction

from django_pagarme.forms import ContactForm
from django_pagarme.models import (
    AUTHORIZED, BOLETO, CREDIT_CARD, PAID, PENDING_REFUND, PROCESSING, PagarmeItemConfig, PagarmeNotification,
    PagarmePayment, PaymentViolation, REFUNDED, REFUSED, UserPaymentProfile, WAITING_PAYMENT,
)

# It's here to be available on facade contract
UserPaymentProfileDoesNotExist = UserPaymentProfile.DoesNotExist

__all__ = [
    'get_payment_item',
    'capture',
    'PaymentViolation',
    'InvalidContactData',
    'ContactForm',
    'PROCESSING',
    'AUTHORIZED',
    'PAID',
    'REFUNDED',
    'PENDING_REFUND',
    'WAITING_PAYMENT',
    'REFUSED',
    'UserPaymentProfileDoesNotExist',
    'ImpossibleUserCreation',
    'BOLETO',
    'CREDIT_CARD',
]


def get_payment_item(slug: str) -> PagarmeItemConfig:
    """
    Find PagarmeItemConfig with its PagarmeFormConfig on database
    :param slug:
    :return: PagarmeItemConfig
    """
    return PagarmeItemConfig.objects.filter(slug=slug).select_related('default_config').get()


def list_payment_item_configs() -> List[PagarmeItemConfig]:
    """
    List PagarmeItemConfig ordered by slug
    :return: list of PagarmeItemConfig
    """
    return list(PagarmeItemConfig.objects.filter().all())


def capture(token: str, django_user_id=None) -> PagarmePayment:
    pagarme_transaction = transaction.find_by_id(token)
    try:
        return find_payment_by_transaction(pagarme_transaction['id'])
    except PagarmePayment.DoesNotExist:
        pass  # payment must be captured
    payment, all_payments_items = PagarmePayment.from_pagarme_transaction(pagarme_transaction)
    captured_transaction = transaction.capture(token, {'amount': payment.amount})
    if django_user_id is None:
        try:
            user = _user_factory(captured_transaction)
        except ImpossibleUserCreation:
            pass
        else:
            django_user_id = user.id

    if django_user_id is not None:
        profile = UserPaymentProfile.from_pagarme_dict(django_user_id, captured_transaction)
        profile.save()
        payment.user_id = django_user_id

    payment.extract_boleto_data(captured_transaction)
    with django_transaction.atomic():
        payment.save()
        payment.items.set(all_payments_items)
        notification = PagarmeNotification(status=captured_transaction['status'], payment=payment)
        notification.save()
    for listener in _payment_status_changed_listeners:
        listener(payment_id=payment.id)
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
    notification = PagarmeNotification(status=current_status, payment_id=payment_id).save()
    for listener in _payment_status_changed_listeners:
        listener(payment_id=payment_id)
    return notification


def find_payment_by_transaction(transaction_id: str) -> PagarmePayment:
    transaction_id = str(transaction_id)
    return PagarmePayment.objects.get(transaction_id=transaction_id)


def find_payment(payment_id: int) -> PagarmePayment:
    return PagarmePayment.objects.get(id=payment_id)


class InvalidNotificationStatusTransition(Exception):
    pass


class InvalidContactData(Exception):
    """
    Class to represent InvalidContactData during validation
    Provides attribute contat_form containing invalid data and error msgs which can be used
    to present them to user on templates or other interfaces
    """

    def __init__(self, contact_form: ContactForm, *args: object) -> None:
        super().__init__(*args)
        self.contact_form: ContactForm = contact_form


_contact_info_listeners = []


def add_contact_info_listener(callable: Callable):
    _contact_info_listeners.append(callable)


def validate_and_inform_contact_info(name, email, phone, payment_item_slug, user=None):
    """
    Validate contact info returning a dict containing normalized values.
    Ex:
        >>> validate_and_inform_contact_info('Foo Bar', 'foo@email.com', '12987654321', 'pytools')
        {'name': 'Foo Bar', 'email':'foo@email.com', 'phone': '+12987654321', 'payment_item_slug': 'pytools'}

    This dict will also be passed to callables configured on add_contact_info_listener.
    Callables must declare parameters with names 'name', 'email', 'phone' and 'payment_item_slug'
    raises InvalidContactData data in case data is invalid
    :param user: Django user
    :param name:
    :param email:
    :param phone:
    :param payment_item_slug: item slug
    :return: dict
    """
    dct = {'name': name, 'email': email, 'phone': phone}
    form = ContactForm(dct)
    if not form.is_valid():
        raise InvalidContactData(contact_form=form)
    data = dict(form.cleaned_data)
    for listener in _contact_info_listeners:
        listener(payment_item_slug=payment_item_slug, user=user, **data)
    return data


def get_user_payment_profile(django_user_or_id):
    """
    Get django user payment profile. Useful to avoid input of customer and billing address data on payment form when user
    decides buying for a second time
    :param django_user_or_id: Django user or his id
    :return: UserPaymentDetails
    """
    User = get_user_model()
    if isinstance(django_user_or_id, User):
        user_id = django_user_or_id.id
    else:
        user_id = django_user_or_id
    return UserPaymentProfile.objects.get(user_id=user_id)


class ImpossibleUserCreation(Exception):
    pass


def _default_factory(pagarme_transaction):
    """
    Default user factory will never create a user
    :param pagarme_transaction:
    :return:
    """
    raise ImpossibleUserCreation()


_user_factory = _default_factory


def set_user_factory(factory: Callable):
    """
    Setup a factory can create a django user after payment capture. Callable receive pagarme transaction api dict
    and can use it on User creation logic
    Must return a Django user or raise ImpossibleUserCreation in case user can't be created.
    :param factory: callable  receiving pagarme transacation as first parameter
    """
    global _user_factory
    _user_factory = factory


def find_payment_item_config(slug: str) -> PagarmeItemConfig:
    return PagarmeItemConfig.objects.get(slug=slug)


_payment_status_changed_listeners = []


def add_payment_status_changed(listener: Callable):
    """
    Listener added with this function will be called receiving PagarmePayment as parameter
    :param listener:
    :return: nothing
    """

    return _payment_status_changed_listeners.append(listener)
