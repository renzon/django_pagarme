from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

one_year_installments_validators = [MaxValueValidator(12), MinValueValidator(1)]


class SellableOption(models.Model):
    name = models.CharField(max_length=128)
    max_installments = models.IntegerField(default=12, validators=one_year_installments_validators)
    default_installment = models.IntegerField(default=1, validators=one_year_installments_validators)
    free_installment = models.IntegerField(default=1, validators=one_year_installments_validators)
    interest_rate = models.FloatField(default=0, validators=[MinValueValidator(0)])
    payments_methods = models.CharField(
        max_length=len('credit_card,boleto'),
        choices=[
            ('boleto', 'Somente Boleto'),
            ('credit_card', 'Somente Cartão de Crédito'),
            ('credit_card,boleto', 'Cartão de Crédito ou Boleto'),
        ],
        default='credit_card,boleto'
    )

    def __str__(self):
        return self.name


class Sellable(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    price = models.PositiveIntegerField('Preço em Centavos')
    tangible = models.BooleanField('Produto físico?')
    default_option = models.ForeignKey(SellableOption, on_delete=models.CASCADE, related_name='sellables')

    def __str__(self):
        return self.name
