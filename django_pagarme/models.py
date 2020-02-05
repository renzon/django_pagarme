from math import ceil

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

one_year_installments_validators = [MaxValueValidator(12), MinValueValidator(1)]

CREDIT_CARD = 'credit_card'
BOLETO = 'boleto'
CREDIT_CARD_AND_BOLETO = f'{CREDIT_CARD},{BOLETO}'


class PaymentConfig(models.Model):
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

    def calculate_amount(self, amount, installments):
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


class PaymentItem(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    price = models.PositiveIntegerField('Preço em Centavos')
    tangible = models.BooleanField('Produto físico?')
    default_config = models.ForeignKey(PaymentConfig, on_delete=models.CASCADE, related_name='payment_items')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Item de Pagamento'
        verbose_name_plural = 'Itens de Pagamento'


class PaymentViolation(Exception):
    """
    Exception for discrepancies on authorization values and respective PaymentConfig and Payment items
    """
    pass


class PagarmePaymentItem(models.Model):
    class Meta:
        unique_together = [['payment', 'item']]

    payment = models.ForeignKey('PagarmePayment', on_delete=models.CASCADE)
    item = models.ForeignKey('PaymentItem', on_delete=models.CASCADE)


class PagarmePayment(models.Model):
    payment_method = models.CharField(
        max_length=max(len(CREDIT_CARD), len(BOLETO)),
        choices=[
            (BOLETO, 'Boleto'),
            (CREDIT_CARD, 'Cartão de Crédito'),
        ],
    )
    amount = models.PositiveIntegerField('Preço pago em Centavos')
    # https://docs.pagar.me/docs/
    # realizando-uma-transacao-de-cartao-de-credito#section-criando-um-cart%C3%A3o-para-one-click-buy
    card_id = models.CharField(max_length=64, null=True, db_index=False)
    card_last_digits = models.CharField(max_length=4, null=True, db_index=False)
    boleto_url = models.TextField(null=True)
    installments = models.IntegerField('Parcelas', validators=[MinValueValidator(1)])
    items = models.ManyToManyField(PaymentItem, through=PagarmePaymentItem, related_name='payments')

    @classmethod
    def from_pagarme_transaction(cls, pagarme_json):
        """
        Crate PagarmePayment from json pagarme transacition json, validating all data
        raise PaymentViolation in case of discrepancies
        :param pagarme_json:
        :return:
        """
        payment_method = pagarme_json['payment_method']
        payment = cls(
            payment_method=payment_method,
            amount=pagarme_json['authorized_amount'],
            card_last_digits=pagarme_json['card_last_digits'],
            installments=pagarme_json['installments'],
        )
        if payment_method == CREDIT_CARD:
            payment.card_id = pagarme_json['card']['id']

        items_ = pagarme_json['items']
        payment_items = payment._validate_items(items_)
        payment_config, first_payment_item = next(payment_items)
        all_payments_items=[first_payment_item]
        all_payments_items.extend(payment_item for _, payment_item in payment_items)
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
        if payment.amount < amount_after_interests:
            raise PaymentViolation(
                f'Parcelamento em {payment.installments} vez(es) com juros {payment_config.interest_rate}% '
                f'deveria dar {amount_after_interests} mas deu {payment.amount}'
            )
        return payment, all_payments_items

    def to_dict(self):
        return {
            'payment_method': self.payment_method,
            'amount': self.amount,
        }

    def _validate_items(self, items_):
        """
        Validate each Pagarme item against respective payment item, yielding PaymentConfig and PaymentItem
        :param items_: pagarme list of items (dicts)
        :return: (PaymentConfig, PaymentItem) generator
        """
        payment_config = None
        for item in items_:
            unit_price = item['unit_price']
            payment_item = PaymentItem.objects.get(slug=item['id'])
            if payment_item.price > unit_price:
                raise PaymentViolation(
                    f'Valor de item {unit_price} é menor que o esperado {payment_item.price}'
                )
            if payment_config is None:
                payment_config = payment_item.default_config
            yield payment_config, payment_item
