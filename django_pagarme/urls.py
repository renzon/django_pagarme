from django.urls import path

from django_pagarme import views

app_name = 'django_pagarme'
urlpatterns = [
    path('capture/<str:token>', views.capture, name='capture'),
    path('obrigado/<slug:slug>', views.thanks, name='thanks'),
    path('notification/<slug:slug>', views.notification, name='notification'),
    path('pagarme/<slug:slug>', views.pagarme, name='pagarme'),
    path('<slug:slug>', views.contact_info, name='contact_info'),
]
