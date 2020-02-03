# django_pagarme
App Django para Automatizar Integração com Gateway de Pagamento Pagarme

## Instalação

Instale via pip

```python
pip isntall django_pagarme
```

## Configure o Django

Configure seu settings.py

```
INSTALLED_APPS = [
    'django_pagarme',
    ...
]

# Dados para integração com Pagarme
CHAVE_PAGARME_API_PRIVADA = 'CHAVE_PAGARME_API_PRIVADA')
CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA = 'CHAVE_PAGARME_CRIPTOGRAFIA_PUBLICA'

```

Rode as migrações

```
python manage.py migrate
```

## Opções gerais de pagamento

As opcões gerais ficam disponíveis via admin do django. Você pode criar várias.
Cada uma deve conter as configurações básicas de pagamento:

Um nome para identificar a opção
Número máximo de parcelas
Escolha padrão do número parcelas que vai aparecer no formulário
Número máximo de parcelas sem juros
Taxa de juros
Método de pagamento: Cartão, Boleto ou ambos.

Segue exemplo:

![Admin de Opções de Pagamento](./documentation/imgs/SellableOptionAdmin.png?raw=true)

## Definição de Produtos

Use o admin para definir demais condições do seu produto:
Nome do produto
Preço em Centavos
Se o produto é físico ou não
Opção padrão de pagamento

Segue exemplo de um curso chamado Pytools custando R$ 99.99

![Admin de Produto](./documentation/imgs/SellableAdmin.png?raw=true)

## Mostrando um pagamento:

Crie uma view buscando pelo produto a ser vendido:

```
from django_pagarme import facade

def produto(request, slug: str):
    ctx = {'sellable': facade.get_sellable(slug)}
    return render(request, 'pagamentos/produto.html', ctx)
```

No seu template, carregue as templates tags do django pagarme e mostre seu formulário:
```
{% load django_pagarme %}
<html>
<head>
    <!-- SCRIPT PAGAR.ME -->
    <script src="//assets.pagar.me/checkout/1.1.0/checkout.js"></script>
    <script src="//code.jquery.com/jquery-3.4.1.js"
            integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU="
            crossorigin="anonymous"></script>
</head>
<body>
<button id="pay-button">Abrir modal de pagamento</button>
{% show_pagarme sellable %}
</body>
</html>
```

Pronto, seu pagamento já está funcionado!!

Um exemplo completo de aplicação se encontra no diretório `exemplo`


## Contribuidores

@renzon

## Como Contribuir

Seguimos a convenção de código da [PEP8](https://www.python.org/dev/peps/pep-0008/), com excessão do tamanho máximo de
linha que pode ter 120 caracteres.

Faça um fork do projeto e mande um pull request. PR sem testes serão rejeitados.
