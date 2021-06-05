from typing import Callable, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction as django_transaction
from django.urls import reverse
from pagarme import postback, transaction, authentication_key

from django_pagarme.forms import ContactForm
from django_pagarme.models import (
    AUTHORIZED, BOLETO, CREDIT_CARD, PAID, PENDING_REFUND, PROCESSING, PagarmeItemConfig, PagarmeNotification,
    PagarmePayment, PaymentViolation, REFUNDED, REFUSED, UserPaymentProfile, WAITING_PAYMENT, PagarmePaymentItem,
)

# It's here to be available on facade contract
UserPaymentProfileDoesNotExist = UserPaymentProfile.DoesNotExist
PagarmePaymentItemDoesNotExist = PagarmePaymentItem.DoesNotExist

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
    'PagarmePaymentItemDoesNotExist',
    'ImpossibleUserCreation',
    'BOLETO',
    'CREDIT_CARD',
]

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


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


class TokenDifferentFromTransactionIdxception(Exception):
    def __init__(self, token, transaction_id) -> None:
        super().__init__()
        self.transaction_id = transaction_id
        self.token = token


def capture(token: str, django_user_id=None) -> PagarmePayment:
    pagarme_transaction = transaction.find_by_id(token)
    transaction_id = pagarme_transaction['id']
    if str(transaction_id) != token:
        raise TokenDifferentFromTransactionIdxception(token, transaction_id)
    try:
        payment = find_payment_by_transaction(transaction_id)
        if payment.status() != AUTHORIZED:  # only status capturing makes sense
            return payment
    except PagarmePayment.DoesNotExist:
        payment, all_payments_items = PagarmePayment.from_pagarme_transaction(pagarme_transaction)
        if django_user_id is None:
            try:
                user = _user_factory(pagarme_transaction)
            except ImpossibleUserCreation:
                pass
            else:
                django_user_id = user.id

        if django_user_id is not None:
            profile = UserPaymentProfile.from_pagarme_dict(django_user_id, pagarme_transaction)
            profile.save()

        payment.user_id = django_user_id
        with django_transaction.atomic():
            payment.save()
            payment.items.set(all_payments_items)

    captured_transaction = transaction.capture(token, {'amount': payment.amount})
    payment.extract_boleto_data(captured_transaction)
    payment.save()
    _save_notification(payment.id, captured_transaction['status'])
    return payment


def handle_notification(transaction_id: str, current_status: str, raw_body: str,
                        expected_signature: str, pagarme_notification_dict) -> PagarmeNotification:
    if not postback.validate(expected_signature, raw_body):
        raise PaymentViolation('')
    try:
        payment_id = PagarmePayment.objects.values_list('id').get(transaction_id=transaction_id)[0]
    except PagarmePayment.DoesNotExist:
        transaction_dict = to_pagarme_transaction(pagarme_notification_dict)
        pagarme_payment, all_payments_items = PagarmePayment.from_pagarme_transaction(transaction_dict)
        try:
            user = _user_factory(transaction_dict)
        except ImpossibleUserCreation:
            pass
        else:
            pagarme_payment.user_id = user.id
            profile = UserPaymentProfile.from_pagarme_dict(user.id, transaction_dict)
            profile.save()

        with django_transaction.atomic():
            pagarme_payment.save()
            pagarme_payment.items.set(all_payments_items)
        payment_id = pagarme_payment.id
    return _save_notification(payment_id, current_status)


def to_pagarme_transaction(pagarme_notification_dict: dict) -> dict:
    """
    Tranform from notification dict to transaction git
    """
    return {
        'status': pagarme_notification_dict['current_status'],
        'payment_method': pagarme_notification_dict['transaction[payment_method]'],
        'authorized_amount': int(pagarme_notification_dict['transaction[authorized_amount]']),
        'card_last_digits': pagarme_notification_dict.get('transaction[card][last_digits]'),
        'installments': int(pagarme_notification_dict['transaction[installments]']),
        'id': pagarme_notification_dict['transaction[id]'],
        'card': {
            'id': pagarme_notification_dict.get('transaction[card][id]')
        },
        'items': [
            {
                'id': pagarme_notification_dict['transaction[items][0][id]'],
                'unit_price': int(pagarme_notification_dict['transaction[items][0][unit_price]']),
            }

        ],
        'customer': {
            'object': pagarme_notification_dict['transaction[customer][object]'],
            'id': pagarme_notification_dict['transaction[customer][id]'],
            'external_id': pagarme_notification_dict['transaction[customer][external_id]'],
            'type': pagarme_notification_dict['transaction[customer][type]'],
            'country': pagarme_notification_dict['transaction[customer][country]'],
            'document_number': pagarme_notification_dict['transaction[customer][document_number]'],
            'document_type': pagarme_notification_dict['transaction[customer][document_type]'],
            'name': pagarme_notification_dict['transaction[customer][name]'],
            'email': pagarme_notification_dict['transaction[customer][email]'],
            'phone_numbers': [
                pagarme_notification_dict['transaction[customer][phone_numbers][0]']
            ],
            'born_at': pagarme_notification_dict['transaction[customer][born_at]'],
            'birthday': pagarme_notification_dict['transaction[customer][birthday]'],
            'gender': pagarme_notification_dict['transaction[customer][gender]'],
            'date_created': pagarme_notification_dict['transaction[customer][date_created]'],
            'documents': [{
                'object': pagarme_notification_dict['transaction[customer][documents][0][object]'],
                'id': pagarme_notification_dict['transaction[customer][documents][0][id]'],
                'type': pagarme_notification_dict['transaction[customer][documents][0][type]'],
                'number': pagarme_notification_dict['transaction[customer][documents][0][number]'],
            }]
        },
        'billing': {
            'object': pagarme_notification_dict['transaction[billing][object]'],
            'id': pagarme_notification_dict['transaction[billing][id]'],
            'name': pagarme_notification_dict['transaction[billing][name]'],
            'address': {
                'object': pagarme_notification_dict['transaction[billing][address][object]'],
                'street': pagarme_notification_dict['transaction[billing][address][street]'],
                'complementary': pagarme_notification_dict['transaction[billing][address][complementary]'],
                'street_number': pagarme_notification_dict['transaction[billing][address][street_number]'],
                'neighborhood': pagarme_notification_dict['transaction[billing][address][neighborhood]'],
                'city': pagarme_notification_dict['transaction[billing][address][city]'],
                'state': pagarme_notification_dict['transaction[billing][address][state]'],
                'zipcode': pagarme_notification_dict['transaction[billing][address][zipcode]'],
                'country': pagarme_notification_dict['transaction[billing][address][country]'],
                'id': pagarme_notification_dict['transaction[billing][address][id]'],
            }
        }

    }


_impossible_states = {
    PROCESSING: {PROCESSING},
    AUTHORIZED: {REFUNDED, REFUSED},
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


def get_user_payment_profile(django_user_or_id) -> UserPaymentProfile:
    """
    Get django user payment profile. Useful to avoid input of customer and billing address data on payment
    form when user
    decides buying for a second time
    :param django_user_or_id: Django user or his id
    :return: UserPaymentProfile
    """
    User = get_user_model()
    if isinstance(django_user_or_id, User):
        user_id = django_user_or_id.pk
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


def one_click_buy(payment_item_config_slug: PagarmeItemConfig, user):
    """
    Create Transaction
    https://docs.pagar.me/reference#criar-transacao
    """
    item = get_payment_item(payment_item_config_slug)
    form_config = item.default_config
    profile = get_user_payment_profile(user)
    domain = settings.ALLOWED_HOSTS[0]
    notification_path = reverse('django_pagarme:notification', kwargs={'slug': item.slug})
    postback_url = f'https://{domain}{notification_path}'
    payment_data = {
        'amount': item.price,
        'card_id': profile.card_id,
        'payment_method': 'credit_card',
        'postback_url': postback_url,
        'async': False,
        'installments': form_config.max_installments,
        'soft_descriptor': 'pythopro',
        'capture': True,
        'customer': profile.to_customer_api_dict(),
        'billing': profile.to_billing_dict(),
        'items': [item.to_dict()]
    }

    return transaction.create(payment_data)


def is_payment_config_item_available(payment_item_config: PagarmeItemConfig, request) -> bool:
    """
    Global var that can be overwitten by user. Must return True if config item is available and False otherwise
    """
    return payment_item_config.is_available()


def set_available_payment_config_item_strategy(strategy: Callable):
    global is_payment_config_item_available
    is_payment_config_item_available = strategy
