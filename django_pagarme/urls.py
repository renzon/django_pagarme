from django.urls import path

from django_pagarme import views

app_name = 'django_pagarme'
urlpatterns = [
    path('capture', views.capture, name='capture'),
    path('notification', views.notification, name='notification'),
]
