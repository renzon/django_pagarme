from collections import ChainMap
from logging import Logger

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt

from django_pagarme import facade
from django_pagarme.facade import InvalidNotificationStatusTransition
from django_pagarme.models import PaymentViolation

logger = Logger(__file__)


def contact_info(request, slug):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            try:
                payment_profile = facade.get_user_payment_profile(user.id)
            except facade.UserPaymentProfileDoesNotExist:
                form = facade.ContactForm({'name': user.first_name, 'email': user.email})
            else:
                form = facade.ContactForm(
                    {'name': payment_profile.name, 'email': payment_profile.email, 'phone': payment_profile.phone}
                )
        else:
            form = facade.ContactForm()
        ctx = {'contact_form': form, 'slug': slug}
        return render(request, 'django_pagarme/contact_form.html', ctx)

    dct = {key: request.POST[key] for key in 'name phone email'.split()}
    dct['payment_item_slug'] = slug
    try:
        dct = facade.validate_and_inform_contact_info(user=request.user, **dct)
    except facade.InvalidContactData as e:
        ctx = {'contact_form': e.contact_form, 'slug': slug}
        resp = render(request, 'django_pagarme/contact_form_errors.html', ctx, status=400)
        return resp
    else:
        path = reverse('django_pagarme:pagarme', kwargs={'slug': slug})
        dct['open_modal'] = 'true'
        query_string = urlencode(dct)
        return redirect(f'{path}?{query_string}')


def capture(request, slug, token):
    try:
        payment = facade.capture(token, request.user.id)
    except facade.PaymentViolation as e:
        logger.exception(str(e))
        return HttpResponseBadRequest()
    else:
        if payment.payment_method == facade.BOLETO:
            ctx = {'payment': payment}
            return render(request, 'django_pagarme/show_boleto_data.html', ctx)
        else:
            return redirect(reverse('django_pagarme:thanks', kwargs={'slug': slug}))


def thanks(request, slug):
    ctx = {'payment_item_config': facade.find_payment_item_config(slug)}
    return render(request, 'django_pagarme/thanks.html', ctx)


@csrf_exempt
def notification(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed([request.method])

    raw_body = request.body.decode('utf8')
    expected_signature = request.headers.get('X-Hub-Signature', '')
    transaction_id = request.POST['transaction[id]']
    current_status = request.POST['current_status']
    try:
        facade.handle_notification(transaction_id, current_status, raw_body, expected_signature, request.POST)
    except PaymentViolation:
        return HttpResponseBadRequest()
    except InvalidNotificationStatusTransition:
        pass

    return HttpResponse()


def pagarme(request, slug):
    open_modal = request.GET.get('open_modal', '').lower() == 'true'
    customer_qs_data = {k: request.GET.get(k, '') for k in ['name', 'email', 'phone']}
    customer_qs_data = {k: v for k, v in customer_qs_data.items() if v}
    user = request.user
    address = None
    if user.is_authenticated:
        user_data = {'external_id': user.id, 'name': user.first_name, 'email': user.email}
        try:
            payment_profile = facade.get_user_payment_profile(user)
        except facade.UserPaymentProfileDoesNotExist:
            customer = ChainMap(customer_qs_data, user_data)
        else:
            customer = ChainMap(customer_qs_data, payment_profile.to_customer_dict(), user_data)
            address = payment_profile.to_billing_address_dict()
    else:
        customer = customer_qs_data
    ctx = {
        'payment_item': facade.get_payment_item(slug),
        'open_modal': open_modal,
        'customer': customer,
        'slug': slug,
        'address': address
    }
    return render(request, 'django_pagarme/pagarme.html', ctx)
