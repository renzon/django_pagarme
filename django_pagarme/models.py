from math import ceil
from types import GeneratorType

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField

one_year_installments_validators = [MaxValueValidator(12), MinValueValidator(1)]

CREDIT_CARD = 'credit_card'
BOLETO = 'boleto'
CREDIT_CARD_AND_BOLETO = f'{CREDIT_CARD},{BOLETO}'
NORMALIZED_BRAZIL_CODE = {'Brasil': 'br'}


class PagarmeFormConfig(models.Model):
    name = models.CharField(max_length=128)
    max_installments = models.IntegerField(default=12, validators=one_year_installments_validators)
    default_installment = models.IntegerField(default=1, validators=one_year_installments_validators)
    free_installment = models.IntegerField(default=1, validators=one_year_installments_validators)
    interest_rate = models.FloatField(default=0, validators=[MinValueValidator(0)])
    payments_methods = models.CharField(
        max_length=len('credit_card,boleto'),
        choices=[
            (BOLETO, 'Somente Boleto'),
            (CREDIT_CARD, 'Somente Cartão de Crédito'),
            (CREDIT_CARD_AND_BOLETO, 'Cartão de Crédito ou Boleto'),
        ],
        default='credit_card,boleto'
    )

    class Meta:
        verbose_name = 'Configuração de Pagamento'
        verbose_name_plural = 'Configurações de Pagamento'

    def __str__(self):
        return self.name

    def calculate_amount(self, amount: int, installments: int) -> int:
        """
        Check pagarme
        https://docs.pagar.me/reference#calculando-pagamentos-parcelados
        :param amount:
        :param installments:
        :return:
        """
        if installments <= self.free_installment:
            return amount
        return ceil(amount * (1 + self.interest_rate * installments / 100))

    def max_amount_after_interest(self, amount: int) -> int:
        return self.calculate_amount(amount, self.max_installments)

    def max_installment_amount_after_interest(self, amount: int) -> int:
        return self.max_amount_after_interest(amount) // self.max_installments

    def payment_plans(self, amount: int) -> GeneratorType:
        """
        Returns all payment plans as a generator tuples of for (installments, amount, installment_amount)
        :param amount:
        :return:
        """
        for i in range(1, self.max_installments + 1):
            calculated_amount = self.calculate_amount(amount, i)
            installment_amount = calculated_amount // i
            yield i, calculated_amount, installment_amount


class PagarmeItemConfig(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(db_index=True, max_length=128)
    price = models.PositiveIntegerField('Preço em Centavos')
    tangible = models.BooleanField('Produto físico?')
    default_config = models.ForeignKey(PagarmeFormConfig, on_delete=models.CASCADE, related_name='payment_items')
    upsell = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, default=None, blank=True)
    available_until = models.DateTimeField('Desativado em', default=None, null=True, blank=True)

    def to_dict(self, quantity=1):
        return {
            'id': self.slug,
            'title': self.name,
            'quantity': quantity,
            'tangible': self.tangible,
            'unit_price': self.price,
        }

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Configuração de Item de Pagamento'
        verbose_name_plural = 'Configurações Itens de Pagamento'

    def max_installments(self):
        return self.default_config.max_installments

    def max_amount_after_interest(self) -> int:
        return self.default_config.max_amount_after_interest(self.price)

    def max_installment_amount_after_interest(self) -> int:
        return self.default_config.max_installment_amount_after_interest(self.price)

    @property
    def payment_plans(self):
        return list(self.default_config.payment_plans(self.price))

    def get_absolute_url(self):
        return reverse('django_pagarme:contact_info', kwargs={'slug': self.slug})

    def get_checkout_url(self):
        return reverse('django_pagarme:pagarme', kwargs={'slug': self.slug})

    def is_available(self):
        if self.available_until is None:
            return True
        return timezone.now() <= self.available_until


class PaymentViolation(Exception):
    """
    Exception for discrepancies on authorization values and respective PagarmeFormConfig and Payment items
    """
    pass


class Plan(models.Model):
    name = models.CharField('Nome do plano', max_length=128)
    slug = models.SlugField(db_index=True, max_length=128)
    amount = models.PositiveIntegerField('Preço em centavos')
    days = models.IntegerField('Prazo em dias para cobrança das parcelas')
    trial_days = models.IntegerField('Dias para teste gratuito do plano', default=0)
    charges = models.IntegerField('Número de cobranças do plano', null=True, default=None)
    invoice_reminder = models.IntegerField('Dias para aviso do vencimento do boleto', null=True, blank=True)
    available_until = models.DateTimeField('Desativado em', default=None, null=True, blank=True)
    pagarme_id = models.CharField('Id do plano no Pagar.me', max_length=255, null=True, blank=True)
    payment_methods = models.CharField(
        'Formas de pagamento',
        max_length=len('credit_card,boleto'),
        choices=[
            (BOLETO, 'Somente Boleto'),
            (CREDIT_CARD, 'Somente Cartão de Crédito'),
            (CREDIT_CARD_AND_BOLETO, 'Cartão de Crédito ou Boleto'),
        ],
        default='credit_card,boleto'
    )

    class Meta:
        verbose_name = 'Plano de assinatura'
        verbose_name_plural = 'Planos de assinatura'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('django_pagarme:subscription', kwargs={'slug': self.slug})

    def is_available(self):
        if self.available_until is None:
            return True
        return timezone.now() <= self.available_until

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


PROCESSING = 'processing'
AUTHORIZED = 'authorized'
PAID = 'paid'
REFUNDED = 'refunded'
PENDING_REFUND = 'pending_refund'
WAITING_PAYMENT = 'waiting_payment'
REFUSED = 'refused'
TRIALING = 'trialing'
PENDING_PAYMENT = 'pending_payment'
ENDED = 'ended'
UNPAID = 'unpaid'
CANCELED = 'canceled'


class Subscription(models.Model):
    pagarme_id = models.CharField('Id da assinatura no Pagar.me', max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=max(len(CREDIT_CARD), len(BOLETO)),
        choices=[
            (BOLETO, 'Boleto'),
            (CREDIT_CARD, 'Cartão de Crédito'),
        ],
    )
    card_id = models.CharField(max_length=64, null=True, db_index=False)
    card_last_digits = models.CharField(max_length=4, null=True, db_index=False)
    user = models.ForeignKey(get_user_model(), db_index=True, on_delete=models.DO_NOTHING)
    plan = models.ForeignKey(Plan, db_index=True, on_delete=models.DO_NOTHING)
    initial_status = models.CharField(
        max_length=30,
        choices=[
            (PAID, 'Pago'),
            (TRIALING, 'Experimentando'),
            (PENDING_PAYMENT, 'Pagamento pendente'),
            (UNPAID, 'Pagamento não efetuado no prazo'),
            (ENDED, 'Encerrada'),
            (CANCELED, 'Cancelada'),
        ]
    )

    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'

    def __str__(self):
        return self.pagarme_id

    @property
    def status(self) -> str:
        """
        Get status from subscriptions notifications
        :return: str
        """
        try:
            current_status = self.notifications.order_by('-creation').values('status').first()['status']
        except:
            current_status = self.initial_status
        return current_status


class SubscriptionNotification(models.Model):
    """
    Class representing a subscription event. Generaly from a notification coming from Pagarme
    """
    creation = models.DateTimeField(db_index=True, auto_now_add=True)
    status = models.CharField(max_length=30,
                              choices=[
                                  (PAID, 'Pago'),
                                  (TRIALING, 'Experimentando'),
                                  (PENDING_PAYMENT, 'Pagamento pendente'),
                                  (UNPAID, 'Inadimplente'),
                                  (ENDED, 'Expirada'),
                                  (CANCELED, 'Cancelada'),
                              ])
    subscription = models.ForeignKey(Subscription, db_index=True, on_delete=models.CASCADE, related_name='notifications')

    class Meta:
        ordering = ('-creation',)
        indexes = [models.Index(fields=('-creation', 'subscription'), name='notification_subscrip_creation')]
        verbose_name = 'Notificação de Assinatura'
        verbose_name_plural = 'Notificações de Assinatura'


class PagarmePaymentItem(models.Model):
    class Meta:
        unique_together = [['payment', 'item']]
        verbose_name = 'Item de Pagamento'
        verbose_name_plural = 'Items de Pagamento'

    payment = models.ForeignKey('PagarmePayment', on_delete=models.CASCADE)
    item = models.ForeignKey('PagarmeItemConfig', on_delete=models.CASCADE)


class PagarmePayment(models.Model):
    payment_method = models.CharField(
        max_length=max(len(CREDIT_CARD), len(BOLETO)),
        choices=[
            (BOLETO, 'Boleto'),
            (CREDIT_CARD, 'Cartão de Crédito'),
        ],
    )
    transaction_id = models.CharField(db_index=True, max_length=50, unique=True)
    amount = models.PositiveIntegerField('Preço pago em Centavos')
    # https://docs.pagar.me/docs/
    # realizando-uma-transacao-de-cartao-de-credito#section-criando-um-cart%C3%A3o-para-one-click-buy
    card_id = models.CharField(max_length=64, null=True, db_index=False)
    card_last_digits = models.CharField(max_length=4, null=True, db_index=False)
    boleto_url = models.TextField(null=True)
    boleto_barcode = models.TextField(null=True)
    installments = models.IntegerField('Parcelas', validators=[MinValueValidator(1)])
    items = models.ManyToManyField(PagarmeItemConfig, through=PagarmePaymentItem, related_name='payments')
    user = models.ForeignKey(get_user_model(), db_index=True, on_delete=models.DO_NOTHING, null=True)
    subscription = models.ForeignKey(Subscription, db_index=True, on_delete=models.DO_NOTHING, null=True, related_name='payments')

    class Meta:
        ordering = ('-id',)
        indexes = [
            models.Index(fields=('user', '-id'), name='pagarme_payments_user')
        ]
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

    def __str__(self):
        return self.transaction_id

    def status(self) -> str:
        """
        Get status from payment notifications
        :return: str
        """
        dct = self.notifications.order_by('-creation').values('status').first()
        return dct['status']

    @classmethod
    def from_pagarme_transaction(cls, pagarme_json):
        """
        Create PagarmePayment from json pagarme transaction json, validating all data
        raise PaymentViolation in case of discrepancies
        :param pagarme_json:
        :return:
        """
        payment_method = pagarme_json['payment_method']
        payment = cls(payment_method=payment_method, amount=pagarme_json['authorized_amount'],
                      card_last_digits=pagarme_json['card_last_digits'], installments=pagarme_json['installments'],
                      transaction_id=str(pagarme_json['id']))
        if payment_method == CREDIT_CARD:
            payment.card_id = pagarme_json['card']['id']

        current_status = pagarme_json['status']
        if pagarme_json.get('subscription_id') is not None:
            return payment, None

        all_payments_items, payment_config = payment.payments_items_from_pagarme_json(pagarme_json)
        if current_status == REFUSED:
            return payment, all_payments_items
        item_prices_sum = sum(payment_item.price for payment_item in all_payments_items)
        pagarme_authorized_amount = payment.amount
        if item_prices_sum > payment.amount:
            raise PaymentViolation(
                f'Valor autorizado {pagarme_authorized_amount} é menor que o esperado {item_prices_sum}'
            )
        if payment_config.max_installments < payment.installments:
            raise PaymentViolation(
                f'Parcelamento em {payment.installments} vez(es) é maior que o máximo ' +
                f'{payment_config.max_installments}'
            )
        amount_after_interests = payment_config.calculate_amount(item_prices_sum, payment.installments)
        if payment.amount < (amount_after_interests - 1):
            raise PaymentViolation(
                f'Parcelamento em {payment.installments} vez(es) com juros {payment_config.interest_rate}% '
                f'deveria dar {amount_after_interests} mas deu {payment.amount}'
            )
        return payment, all_payments_items

    @classmethod
    def from_pagarme_subscription(cls, pagarme_json):
        payment_method = pagarme_json['payment_method']
        current_transaction = pagarme_json['current_transaction']
        payment = cls(
            payment_method=payment_method,
            amount=current_transaction['authorized_amount'],
            card_last_digits=current_transaction['card_last_digits'],
            installments=current_transaction['installments'],
            transaction_id=str(current_transaction['id'])
        )

        if payment_method == CREDIT_CARD:
            payment.card_id = pagarme_json['card']['id']

        return payment

    def extract_boleto_data(self, pagarme_json):
        if self.payment_method == BOLETO:
            self.boleto_barcode = pagarme_json['boleto_barcode']
            self.boleto_url = pagarme_json['boleto_url']

    def to_dict(self):
        return {
            'payment_method': self.payment_method,
            'amount': self.amount,
        }

    def _validate_items(self, items_):
        """
        Validate each Pagarme item against respective payment item, yielding PagarmeFormConfig and PagarmeItemConfig
        :param items_: pagarme list of items (dicts)
        :return: (PagarmeFormConfig, PagarmeItemConfig) generator
        """
        payment_config = None
        for item in items_:
            unit_price = item['unit_price']
            payment_item = PagarmeItemConfig.objects.get(slug=item['id'])
            if payment_item.price > unit_price:
                raise PaymentViolation(
                    f'Valor de item {unit_price} é menor que o esperado {payment_item.price}'
                )
            if payment_config is None:
                payment_config = payment_item.default_config
            yield payment_config, payment_item

    def first_item_slug(self):
        item = self.items.first()
        if item is None:
            raise PagarmePaymentItem.DoesNotExist(f'First item of {self} does not exist')
        return item.slug

    def payments_items_from_pagarme_json(self, pagarme_json):
        items_ = pagarme_json['items']
        payment_items = self._validate_items(items_)
        payment_config, first_payment_item = next(payment_items)
        all_payments_items = [first_payment_item]
        all_payments_items.extend(payment_item for _, payment_item in payment_items)
        return all_payments_items, payment_config


class PagarmeNotification(models.Model):
    """
    Class representing a payment event. Generaly from a notification coming from Pagarme
    """
    creation = models.DateTimeField(db_index=True, auto_now_add=True)
    status = models.CharField(max_length=30,
                              choices=[
                                  (PROCESSING, 'Processando'),
                                  (AUTHORIZED, 'Autorizado'),
                                  (PAID, 'Pago'),
                                  (REFUNDED, 'Estornado'),
                                  (PENDING_REFUND, 'Estornando'),
                                  (WAITING_PAYMENT, 'Aguardando Pgto'),
                                  (REFUSED, 'Recusado'),
                              ])
    payment = models.ForeignKey(PagarmePayment, db_index=True, on_delete=models.CASCADE, related_name='notifications')

    class Meta:
        ordering = ('-creation',)
        indexes = [
            models.Index(fields=('-creation', 'payment'), name='notification_payment_creation')
        ]
        verbose_name = 'Notificação de Pagamento'
        verbose_name_plural = 'Notificações de Pagamento'


class UserPaymentProfile(models.Model):
    user = models.OneToOneField(get_user_model(), primary_key=True, on_delete=models.CASCADE)

    card_id = models.CharField(max_length=64, db_index=False, blank=True, null=True, default=None)
    # customer data
    customer_type = models.CharField(max_length=64, db_index=False)
    costumer_country = models.CharField(max_length=64, db_index=False)
    document_number = models.CharField(max_length=64, db_index=False)
    document_type = models.CharField(max_length=64, db_index=False)
    name = models.CharField(max_length=128, db_index=False)
    email = models.CharField(max_length=64, db_index=False)
    phone = PhoneNumberField(db_index=False)

    # Billing Address Data
    street = models.CharField(max_length=128, db_index=False)
    complementary = models.CharField(max_length=128, db_index=False)
    street_number = models.CharField(max_length=128, db_index=False)
    neighborhood = models.CharField(max_length=128, db_index=False)
    city = models.CharField(max_length=128, db_index=False)
    state = models.CharField(max_length=128, db_index=False)
    zipcode = models.CharField(max_length=128, db_index=False)
    address_country = models.CharField(max_length=128, db_index=False)

    class Meta:
        ordering = ('-user_id',)
        verbose_name = 'Perfil de Pagamento '
        verbose_name_plural = 'Perfis de Pagamento'

    def to_customer_dict(self):
        phone_str = str(self.phone)
        return {
            'external_id': str(self.user_id),
            'type': self.customer_type,
            'country': self.costumer_country,
            'document': {
                'number': self.document_number,
                'type': self.document_type,
            },
            'name': self.name,
            'email': self.email,
            'phone': phone_str,
        }

    def to_customer_api_dict(self):
        dct = self.to_customer_dict()
        dct['documents'] = [dct.pop('document')]
        dct['phone_numbers'] = [dct.pop('phone')]
        return dct

    def to_billing_address_dict(self):
        address = {
            'street': self.street,
            'street_number': self.street_number,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'state': self.state,
            'zipcode': self.zipcode,
            'country': self.address_country,
        }
        if self.complementary:
            address['complementary'] = self.complementary
        return address

    def to_billing_dict(self):
        return {'name': self.name, 'address': self.to_billing_address_dict()}

    @classmethod
    def from_pagarme_dict(cls, django_user_id, pagarme_transaction):
        """
        Creates UserPaymentProfile from pagarme api json transaction
        :param django_user_id: django user id
        :param pagarme_transaction: pagarme api transaction dict
        :return: UserPaymentProfile
        """
        customer = pagarme_transaction['customer']
        document = customer['documents'][-1]
        address = pagarme_transaction['billing']['address']
        card = pagarme_transaction.get('card')
        card_id = None if card is None else card.get('id')
        return cls(
            user_id=django_user_id,
            customer_type=customer['type'],
            costumer_country=NORMALIZED_BRAZIL_CODE.get(customer['country'], customer['country']),
            document_number=document['number'],
            document_type=document['type'],
            name=customer['name'],
            email=customer['email'],
            phone=customer['phone_numbers'][-1].replace('+', ''),
            street=address['street'],
            complementary=address.get('complementary', '') or '',
            street_number=address['street_number'],
            neighborhood=address['neighborhood'],
            city=address['city'],
            state=address['state'],
            zipcode=address['zipcode'],
            address_country=NORMALIZED_BRAZIL_CODE.get(address['country'], address['country']),
            card_id=card_id
        )

    @classmethod
    def from_pagarme_subscription(cls, django_user_id, pagarme_subscription):
        """
        Creates UserPaymentProfile from pagarme api json subscription
        :param django_user_id: django user id
        :param pagarme_subscription: pagarme api subscription dict
        :return: UserPaymentProfile
        """
        customer = pagarme_subscription['customer']
        phone = pagarme_subscription['phone']
        address = pagarme_subscription['address']
        card = pagarme_subscription.get('card')
        card_id = None if card is None else card.get('id')
        customer_country = customer['country'] if customer['country'] is not None else address['country']

        return cls(
            user_id=django_user_id,
            customer_type='individual' if customer['type'] is None else customer['type'],
            costumer_country=NORMALIZED_BRAZIL_CODE.get(customer_country, customer_country),
            document_number=customer['document_number'],
            document_type=customer['document_type'],
            name=customer['name'],
            email=customer['email'],
            phone=f'{phone["ddi"]} {phone["ddd"]} {phone["number"]}',
            street=address['street'],
            complementary=address.get('complementary', '') or '',
            street_number=address['street_number'],
            neighborhood=address['neighborhood'],
            city=address['city'],
            state=address['state'],
            zipcode=address['zipcode'],
            address_country=NORMALIZED_BRAZIL_CODE.get(address['country'], address['country']),
            card_id=card_id
        )
