# Create your views here.
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from pagarme import authentication_key, transaction

authentication_key(settings.CHAVE_PAGARME_API_PRIVADA)


def produto(request):
    ctx = {'CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA': settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA}
    return render(request, 'pagamentos/produto.html', ctx)


@csrf_exempt
def captura(request):
    token = request.POST['token']
    transacao = transaction.find_by_id(token)
    valor = transacao['authorized_amount']
    valor_minimo = 8000
    if valor < valor_minimo:
        return HttpResponseBadRequest(f'Valor {valor} menor que o minimo {valor_minimo}')
    transaction.capture(token, {'amount': valor})
    return JsonResponse({'token': 'ok'})
