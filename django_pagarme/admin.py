from django.contrib import admin

from django_pagarme.models import PagarmePayment, PaymentConfig, PaymentItem


@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'tangible', 'default_config')
    list_filter = ('default_config',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PaymentConfig)
class PaymentOptionsAdmin(admin.ModelAdmin):
    pass


@admin.register(PagarmePayment)
class PagarmePaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_method', 'amount', 'card_id', 'card_last_digits', 'boleto_url', 'installments')
    list_filter = ('payment_method', 'items')
