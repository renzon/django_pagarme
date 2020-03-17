import pytest

from django_pagarme import facade


@pytest.fixture
def listener_mock(mocker):
    listener = mocker.Mock()
    facade.add_contact_info_listener(listener)
    yield listener
    facade._contact_info_listeners = []


def test_add_contact_info_listener_success(listener_mock):
    dct = {
        'name': 'Foo Bar', 'email': 'foo@email.com', 'phone': '+5512987654321', 'payment_item_slug': 'pytools',
        'user': None
    }
    facade.validate_and_inform_contact_info('Foo Bar', 'foo@email.com', '12987654321', 'pytools')
    listener_mock.assert_called_once_with(**dct)


def test_add_contact_info_listener_failure(listener_mock):
    with pytest.raises(facade.InvalidContactData):
        facade.validate_and_inform_contact_info('Foo Bar', 'foo@email.com', '129', 'pytools')
    assert listener_mock.call_count == 0
