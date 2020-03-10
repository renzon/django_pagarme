from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from django_pagarme import facade


def home(request):
    if request.method == 'GET':
        form = facade.ContactForm()
        return render(request, 'pagamentos/home.html', {'contact_form': form})

    dct = {key: request.POST[key] for key in 'name phone email'.split()}
    try:
        dct = facade.validate_and_inform_contact_info(**dct)
    except facade.InvalidContactData as e:
        return render(request, 'pagamentos/home.html', {'contact_form': e.contact_form}, status=400)
    else:
        path = reverse('pagamentos:produto', kwargs={'slug': 'pytools'})
        dct['modal'] = 'true'
        query_string = urlencode(dct)

        return redirect(f'{path}?{query_string}')
