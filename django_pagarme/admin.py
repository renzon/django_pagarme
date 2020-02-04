from django.contrib import admin

from django_pagarme.models import PaymentConfig, PaymentItem


@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'tangible', 'default_config')
    list_filter = ('default_config',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PaymentConfig)
class PaymentOptionsAdmin(admin.ModelAdmin):
    pass
