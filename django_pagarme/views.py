from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django_pagarme import facade
from django_pagarme.models import PaymentViolation


def capture(request):
    token = request.POST['token']
    try:
        payment = facade.capture(token, request.user.id)
    except facade.PaymentViolation as violation:
        return JsonResponse({'errors': str(violation)}, status=400)
    else:
        return JsonResponse(payment.to_dict())


@csrf_exempt
def notification(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed([request.method])

    raw_body = request.body.decode('utf8')
    expected_signature = request.headers.get('X-Hub-Signature', '')
    transaction_id = request.POST['transaction[id]']
    current_status = request.POST['current_status']
    try:
        facade.handle_notification(transaction_id, current_status, raw_body, expected_signature)
    except PaymentViolation:
        return HttpResponseBadRequest()

    return HttpResponse()
