from django.http import JsonResponse

from django_pagarme import facade


def capture(request):
    token = request.POST['token']
    try:
        payment=facade.capture(token)
    except facade.PaymentViolation as violation:
        return JsonResponse({'errors': str(violation)}, status=400)
    else:
        return JsonResponse(payment.to_dict())
