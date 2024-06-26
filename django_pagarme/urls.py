from django.urls import path

from django_pagarme import views

app_name = 'django_pagarme'
urlpatterns = [
    path('capture/<slug:slug>/<str:token>', views.capture, name='capture'),
    path('obrigado/<slug:slug>', views.thanks, name='thanks'),
    path('indisponivel/<slug:slug>', views.unavailable, name='unavailable'),
    path('one_click/<slug:slug>', views.one_click, name='one_click'),
    path('notification/<slug:slug>', views.notification, name='notification'),
    path('pagarme/<slug:slug>', views.pagarme, name='pagarme'),
    path('<slug:slug>', views.contact_info, name='contact_info'),
    path('subscription/<slug:slug>', views.subscription, name='subscription'),
    path('subscribe/<slug:slug>', views.subscribe, name='subscribe'),
    path(
        'subscription_payment_bank_slip/<int:transaction_id>',
        views.subscription_payment_bank_slip,
        name='subscription_payment_bank_slip'
    ),
]
