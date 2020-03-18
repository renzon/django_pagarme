# django_pagarme
App Django para Automatizar Integração com Gateway de Pagamento Pagarme



[![codecov](https://codecov.io/gh/renzon/django_pagarme/branch/master/graph/badge.svg)](https://codecov.io/gh/renzon/django_pagarme)



## Instalação

Instale via pip

```python
pip install django_pagarme
```

## Configure o Django

Configure seu settings.py

```
INSTALLED_APPS = [
    'django_pagarme',
    'phonenumber_field',
    ...
]

# Dados para integração com Pagarme
CHAVE_PAGARME_API_PRIVADA = 'CHAVE_PAGARME_API_PRIVADA')
CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA = 'CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA'

# Para validar telefones no Brasil
PHONENUMBER_DEFAULT_REGION = 'BR'

```

Rode as migrações

```
python manage.py migrate
```

Configure as urls:

```python
from django.urls import include, path
...

urlpatterns = [
    path('checkout/', include('django_pagarme.urls')),
    ...
]
```

## Personalize seus formulários

Cria uma app e no diretório de templates, crie suas páginas como descrito abaixo.

### Dados de Contato

Formulário para obter dados de contato do usuário 
 
Template `django_pagarme/contact_form.html`

Ex:
```html
<body>
<form action="{% url 'django_pagarme:contact_info' slug=slug %}" method="post">
    {% csrf_token %}
    {{ contact_form.as_p }}
    <button type="submit">Comprar</button>
</form>
</body>
```

### Formulário de erros

Formulário de erros de dados de contato do usuário.
 
Template `django_pagarme/contact_form_errors.html`

Pode herdar de `contact_form.html` no caso de vc decidir que quer usar a mesma página com formulário

Ex:
```html
{% extends 'django_pagarme/contact_form.html' %}
```

### Página de Checkout do Pagarme

Página onde o usuário preenche os dados de pagamento.
 
Template `django_pagarme/pagarme.html`

Deve ter um elemento clicável com classe css `pay-button`.
Ao clicar nesse elemento, o checkout é iniciado.

Ex:
```html
{% load django_pagarme %}
{% load django_pagarme %}
<html>
<head>
    <!-- SCRIPT PAGAR.ME -->
    <title>{{ payment_item.name }}</title>
    <script src="//assets.pagar.me/checkout/1.1.0/checkout.js"></script>
</head>
<body>
<h1>{{ payment_item.name }}</h1>
<h2>Planos</h2>
<ul>
    {% for installments, amount, installment_amount in payment_item.payment_plans %}
        {% if installments == 1 %}
            <li>{{ amount|cents_to_brl }} a vista</li>
        {% else %}
            <li>{{ amount|cents_to_brl }} em {{ installments }} parcelas de {{ installment_amount|cents_to_brl }}</li>
        {% endif %}
    {% endfor %}
</ul>
<button class="pay-button">Abrir modal de pagamento</button>
{% show_pagarme payment_item customer open_modal %}

</body>
</html>
```

### Página de visualização de Boleto

Página onde o usuário acessa os dados do boleto para pagamento
 
Template `django_pagarme/show_boleto_data.html`

Ex:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dados do Boleto</title>
</head>
<body>
    <h1>Dados do Boleto</h1>
    <p>Código de Barras: {{ payment.boleto_barcode }}</p>
    <iframe src="{{ payment.boleto_url }}"></iframe>
</body>
</html>
```

### Página de obrigado

Página onde o usuário é levado ao finalizar o pagamento
 
Template `django_pagarme/thanks.html`

Ex:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Obrigado por Comprar</title>
</head>
<body>
<h1> Obrigado por comprar {{ payment_item_config.name }}</h1>
</body>
</html>
```



## Listeners

O biblioteca dispo de 2 listener para ouvir eventos e também da configuração de criação de usuário.

### Listener de Contato de usuário

Chamável utilizado para receber os dados do usuário

Ex:
```python
from django_pagarme import facade
def print_contact_info(name, email, phone, payment_item_slug, user=None):
    print('Contact Data:', name, email, phone, payment_item_slug, user)


facade.add_contact_info_listener(print_contact_info)
```

Essa função pode ser usada para armazenar os dados em banco, ou chamar uma api depois que o usuário preenche os dados de contato.

### Fábrica de usuário

Chamável utilizado para gerar um usuário para ser conectado ao pedido.
Só é chamado se não houver usuário logado. Se não for setado, pedidos ainda serão
feitos corretamente, mas sem link com qualquer usuário do sistema.

Ex:
```python
from django_pagarme import facade
from django.contrib.auth import get_user_model


def user_factory(pagarme_transaction):
    User = get_user_model()
    customer = pagarme_transaction['customer']
    try:
        return User.objects.get(email=customer['email'])
    except User.DoesNotExist:
        return User.objects.create(
            first_name=customer['name'],
            email=customer['email']
        )


facade.set_user_factory(user_factory)

```

### Listener de mudanças de status

Toda vez que o sistema recebe notificação de mudança de status, esse chamável
é executado e recebe o id do respectivo pagamento.

Pode ser utilizado para ativa um usuário na base, ou enviar o produto, de acordo
com o status.

Ex:
```python
from django_pagarme import facade


def print_payment_id(payment_id):
    payment = facade.find_payment(payment_id)
    print(payment, payment.status())


facade.add_payment_status_changed(print_payment_id)
```

Os status existentes estão disponíveis via fachada (facade):

```python
PROCESSING = 'processing'
AUTHORIZED = 'authorized'
PAID = 'paid'
REFUNDED = 'refunded'
PENDING_REFUND = 'pending_refund'
WAITING_PAYMENT = 'waiting_payment'
REFUSED = 'refused'
```



### Configuração de Pagamento

As configurações ficam disponíveis via admin do django. Você pode criar várias.
Cada uma deve conter as configurações básicas de pagamento:

Um nome para identificar a opção
Número máximo de parcelas
Escolha padrão do número parcelas que vai aparecer no formulário
Número máximo de parcelas sem juros
Taxa de juros
Método de pagamento: Cartão, Boleto ou ambos.

Segue exemplo:

![Admin de Opções de Pagamento](./documentation/imgs/PaymentFormConfig.png?raw=true)

### Configuração de Item de Pagamento

Aqui vc configura os produtos que vai vender. Propriedades:

Nome do pagarme
Preço em Centavos
Se o pagarme é físico ou não
Opção padrão de pagamento

Segue exemplo de um curso chamado Pytools custando R$ 97.00

![Admin de Produto](./documentation/imgs/PaymentFormItemConfig.png?raw=true)

Uma Configuração geral serve como configuração padrão de um item

### Outras classes de interesse

No admin ainda existem 4 classes de interesse:

1. PagarmePayment : reprensenta um pagamento (transction) do pagarme
1. PagarmeNotification: representa uma notificacão do pagarme. Um pagamento pode possuir múltiplas notificações  
1. UserPaymentProfile: representa dados gerais preenchidos no último checkout feito no pagarme. É usado para preencher os dados em um próximo pagamento e está relacioando com o usuário Django.
1.    


Um exemplo completo de aplicação se encontra no diretório `exemplo`


## Contribuidores

@renzon

## Como Contribuir

Seguimos a convenção de código da [PEP8](https://www.python.org/dev/peps/pep-0008/), com excessão do tamanho máximo de
linha que pode ter 120 caracteres.

Faça um fork do projeto e mande um pull request. PR sem testes serão rejeitados.

Para rodar o projeto de exemplo:

Instale o docker
Rode o Banco de Dados: `docker-compose -f docker-compose.yml up -d`
Crie um arquivo `.env` dentro da pasta `exemplo`:

```
CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA=coloque_sua_chave_publica_aqui
CHAVE_PAGARME_API_PRIVADA=coloque_sua_chave_privada_aqui
PHONENUMBER_DEFAULT_REGION=BR
DATABASE_URL=postgres://postgres:postgres@localhost:5432/django_pagarme
``` 
Obs: Troque as chaves do pagarme pelas suas chaves do [ambiente de teste](https://docs.pagar.me/docs/api-key-e-encryption-key) para testar localmente.

Se for rodar em computador local, use um serviço como o [ngrok](https://ngrok.com/) para mapear suas portas locais na internet

Instale o pipenv:

```
python -m pip install pipenv
``` 

Navegue até a pasta exemplo e rode:

```
pipenv sync
```

Rode o servidor local:
```
pipenv run python manage.py runserver
```

Para rodar os testes:
```
exemplo $ pipenv run pytest .
Loading .env environment variables…
======================================================= test session starts ========================================================
platform darwin -- Python 3.8.0, pytest-5.3.5, py-1.8.1, pluggy-0.13.1
django: settings: base.settings (from ini)
rootdir: /Users/renzo/PycharmProjects/django_pagarme, inifile: setup.cfg
plugins: mock-2.0.0, cov-2.8.1, django-3.8.0
collected 85 items                                                                                                                 

base/tests/test_home.py .                                                                                                    [  1%]
pagamentos/tests/test_captura_boleto.py ............                                                                         [ 15%]
pagamentos/tests/test_captura_credit_card.py ..............                                                                  [ 31%]
pagamentos/tests/test_dados_usuario.py ........                                                                              [ 41%]
pagamentos/tests/test_pagarme_notification_transitions.py ................                                                   [ 60%]
pagamentos/tests/test_pagarme_notifications.py ....                                                                          [ 64%]
pagamentos/tests/test_pagina_pagamento.py ..................                                                                 [ 85%]
pagamentos/tests/test_thanks.py ..                                                                                           [ 88%]
base/tests/test_contact_info.py ........                                                                                     [ 97%]
base/tests/test_facade.py ..                                                                                                 [100%]

======================================================== 85 passed in 9.26s ======================================================== 
```




