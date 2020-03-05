from django.contrib import admin

from django_pagarme.models import PagarmeNotification, PagarmePayment, PagarmeFormConfig, PagarmeItemConfig


@admin.register(PagarmeItemConfig)
class PagarmeItemConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'tangible', 'default_config')
    list_filter = ('default_config',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PagarmeFormConfig)
class PagarmeFormConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(PagarmePayment)
class PagarmePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'payment_method',
        'amount',
        'card_id',
        'card_last_digits',
        'boleto_url',
        'installments'
    )
    list_filter = ('payment_method', 'items')


@admin.register(PagarmeNotification)
class PagarmeNotificationAdmin(admin.ModelAdmin):
    list_display = ('payment', 'status', 'creation')
    list_filter = ('payment',)
    ordering = ('payment', '-creation')
