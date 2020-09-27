from django.contrib import admin
from django.utils.safestring import mark_safe

from django_pagarme.models import (
    PagarmeFormConfig, PagarmeItemConfig, PagarmeNotification, PagarmePayment, UserPaymentProfile, Plan, Subscription, SubscriptionNotification
)


@admin.register(PagarmeItemConfig)
class PagarmeItemConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'tangible', 'default_config', 'contact_form', 'checkout', 'available_until')
    list_filter = ('default_config',)
    prepopulated_fields = {'slug': ('name',)}

    def contact_form(self, pagarme_item_config: PagarmeItemConfig):
        return mark_safe(f'<a href="{pagarme_item_config.get_absolute_url()}">Contact Form</a>')

    contact_form.short_description = 'contact form'

    def checkout(self, pagarme_item_config: PagarmeItemConfig):
        return mark_safe(f'<a href="{pagarme_item_config.get_checkout_url()}">Checkout</a>')

    checkout.short_description = 'checkout'

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PagarmeFormConfig)
class PagarmeFormConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(PagarmePayment)
class PagarmePaymentAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_display = (
        'user',
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
    search_fields = ('payment__transaction_id__exact',)
    ordering = ('payment', '-creation')


@admin.register(UserPaymentProfile)
class UserPaymentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email', 'phone')
    search_fields = ('email', 'user__email')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'amount', 'days', 'payment_methods', 'available_until')
    readonly_fields = (
        'name',
        'amount',
        'days',
        'trial_days',
        'charges',
        'invoice_reminder',
        'pagarme_id',
        'payment_methods',
    )

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'payment_method',
        'card_id',
        'card_last_digits',
        'status',
    )

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SubscriptionNotification)
class SubscriptionNotificationAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'status', 'creation')
    search_fields = ('subscription__pagarme_id__exact',)
    ordering = ('subscription', '-creation')
