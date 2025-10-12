import pytest
from django.contrib.auth import get_user_model  # pylint: disable=ungrouped-imports
from django.test.client import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_login_failed_email_validation(client: Client):
    payload = {
        'email': '',
        'password': 'thanks123',
    }
    resp = client.post(reverse('rest_login'), data=payload)
    assert resp.status_code == 400, resp.json()


def test_user_signup(client: Client):
    payload = {
        'email': 'testuser@gmail.com',
        'password1': 'randompassword123',
        'password2': 'randompassword123',
    }

    resp = client.post(reverse('rest_register'), data=payload, status_code=201)
    assert resp.status_code == 201, resp.json()
    assert User.objects.filter(email=payload['email']).exists()
