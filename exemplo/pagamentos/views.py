# Create your views here.
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def produto(request):
    ctx = {'CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA': settings.CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA}
    return render(request, 'pagamentos/produto.html', ctx)


@csrf_exempt
def captura(request):
    return JsonResponse({'token': 'ok'})
