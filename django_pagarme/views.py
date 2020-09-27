import json
from collections import ChainMap
from logging import Logger

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt

from django_pagarme import facade
from django_pagarme.facade import InvalidNotificationStatusTransition
from django_pagarme.models import PaymentViolation, Plan

logger = Logger(__file__)


def contact_info(request, slug):
    payment_item = facade.get_payment_item(slug)
    if not facade.is_payment_config_item_available(payment_item, request):
        return redirect(reverse('django_pagarme:unavailable', kwargs={'slug': slug}))
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
    except facade.TokenDifferentFromTransactionIdxception as e:
        return redirect(
            reverse('django_pagarme:capture', kwargs={'slug': slug, 'token': e.transaction_id}),
            permanent=True
        )
    else:
        if payment.payment_method == facade.BOLETO:
            ctx = {'payment': payment, 'upsell': facade.get_payment_item(slug).upsell}
            suffix = slug.replace('-', '_')
            templates = [
                f'django_pagarme/show_boleto_data_{suffix}.html',
                'django_pagarme/show_boleto_data.html'
            ]

            return render(request, templates, ctx)
        else:
            return redirect(reverse('django_pagarme:thanks', kwargs={'slug': slug}))


def thanks(request, slug):
    suffix = slug.replace('-', '_')
    try:
        ctx = {'plan': facade.get_plan(slug)}
        templates = [
            f'django_pagarme/thanks_plan_{suffix}.html',
            'django_pagarme/thanks_plan.html'
        ]
    except Plan.DoesNotExist:
        ctx = {'payment_item_config': facade.find_payment_item_config(slug)}
        templates = [
           f'django_pagarme/thanks_{suffix}.html',
           'django_pagarme/thanks.html'
        ]

    return render(request, templates, ctx)


def one_click(request, slug):
    if request.method != 'POST':
        return redirect(reverse('django_pagarme:pagarme', kwargs={'slug': slug}))
    try:
        facade.one_click_buy(slug, request.user)
    except Exception:
        path = reverse('django_pagarme:pagarme', kwargs={'slug': slug})
        return redirect(f'{path}?open_modal=true&review_informations=false')
    else:
        return redirect(reverse('django_pagarme:thanks', kwargs={'slug': slug}))


@csrf_exempt
def notification(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed([request.method])

    raw_body = request.body.decode('utf8')
    expected_signature = request.headers.get('X-Hub-Signature', '')
    current_status = request.POST['current_status']
    event = request.POST['event']
    if event == 'subscription_status_changed':
        subscription_id = request.POST['subscription[id]']
        try:
            facade.handle_subscription_notification(
               subscription_id, current_status, raw_body, expected_signature, request.POST
            )
        except Exception:
            return HttpResponseBadRequest()

    else:
        transaction_id = request.POST['transaction[id]']
        try:
            facade.handle_notification(transaction_id, current_status, raw_body, expected_signature, request.POST)
        except PaymentViolation:
            return HttpResponseBadRequest()
        except InvalidNotificationStatusTransition:
            pass

    return HttpResponse()


def pagarme(request, slug):
    payment_item = facade.get_payment_item(slug)
    if not facade.is_payment_config_item_available(payment_item, request):
        return redirect(reverse('django_pagarme:unavailable', kwargs={'slug': slug}))
    open_modal = request.GET.get('open_modal', '').lower() == 'true'
    review_informations = not (request.GET.get('review_informations', '').lower() == 'false')
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
        'payment_item': payment_item,
        'open_modal': open_modal,
        'review_informations': review_informations,
        'customer': customer,
        'slug': slug,
        'address': address
    }
    suffix = slug.replace('-', '_')
    templates = [
        f'django_pagarme/pagarme_{suffix}.html',
        'django_pagarme/pagarme.html'
    ]

    return render(request, templates, ctx)


def unavailable(request, slug):
    try:
        context = {'plan': facade.get_plan(slug)}
        template_name = 'django_pagarme/unavailable_plan.html'
    except Plan.DoesNotExist:
        try:
            context = {'payment_item_config': facade.get_payment_item(slug)}
            template_name = 'django_pagarme/unavailable_payment_item.html'
        except PaymentItemConfig.DoesNotExist:
            raise Http404
    return render(request, template_name, context)


def subscription(request, slug):
    plan = facade.get_plan(slug)
    if not plan.is_available():
        return redirect(reverse('django_pagarme:unavailable', kwargs={'slug': slug}))
    open_modal = request.GET.get('open_modal', '').lower() == 'true'
    review_informations = not (request.GET.get('review_informations', '').lower() == 'false')
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
        'plan': plan,
        'open_modal': open_modal,
        'review_informations': review_informations,
        'customer': customer,
        'slug': slug,
        'address': address
    }
    suffix = slug.replace('-', '_')
    templates = [
        f'django_pagarme/subscription_{suffix}.html',
        'django_pagarme/subscription.html'
    ]

    return render(request, templates, ctx)


@csrf_exempt
def subscribe(request, slug):
    plan = facade.get_plan(slug)
    payload = json.loads(request.body)
    try:
        payment = facade.create_subscription(plan, payload, request.user.id)
        if payment.payment_method == facade.BOLETO:
            callback_url = reverse(
                'django_pagarme:subscription_payment_bank_slip',
                kwargs={'transaction_id': payment.transaction_id}
            )
        else:
            callback_url = reverse('django_pagarme:thanks', kwargs={'slug': slug})
    except Exception:
        return HttpResponseBadRequest()

    return HttpResponse(callback_url)


def subscription_payment_bank_slip(request, transaction_id):
    payment = facade.find_payment_by_transaction(transaction_id)
    suffix = payment.subscription.plan.slug.replace('-', '_')
    templates = [
        f'django_pagarme/show_boleto_data_{suffix}.html',
        'django_pagarme/show_boleto_data.html'
    ]
    return render(request, templates, {'payment': payment})
