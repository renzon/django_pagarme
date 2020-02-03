from django.contrib import admin

from django_pagarme.models import Sellable, SellableOption


@admin.register(Sellable)
class SellableAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'tangible', 'default_option')
    list_filter = ('default_option',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SellableOption)
class SellableOptionAdmin(admin.ModelAdmin):
    pass
