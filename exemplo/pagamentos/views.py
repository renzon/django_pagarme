# Create your views here.
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def produto(request):
    return render(request, 'pagamentos/produto.html')


@csrf_exempt
def captura(request):
    return JsonResponse({'token': 'ok'})
