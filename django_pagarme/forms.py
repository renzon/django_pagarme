from django import forms
from phonenumber_field.formfields import PhoneNumberField


class ContactForm(forms.Form):
    name = forms.CharField(max_length=64, label='Nome Completo')
    email = forms.EmailField()
    phone = PhoneNumberField(label='Celular')
