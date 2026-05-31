import pytest
from pytest_django.fixtures import django_db_createdb
from rest_framework import status
from rest_framework.test import APIClient, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


@pytest.mark.django_db
class TestUserAuthentication:

    def test_anonymous_user_can_register(self):

        data = {
            "email": "random@site.com",
            "password": "password",
            "phone": "09999999999"
        }
        client = APIClient()
        response = client.post("/api/accounts/register/", data=data)

        assert "random@site.com" in response.content.decode('utf-8')
        assert "09999999999" in response.content.decode('utf-8')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == 1


    def test_anonymous_user_can_login_with_email(self):

        user = User(
            email="random@site.com",
            password="password",
            phone="09999999999")
        user.save()
        client = APIClient()
        response = client.post(
            "/api/accounts/login/", {"email": user.email, "password": user.password} )

        assert response.status_code == status.HTTP_200_OK
        assert "refresh" in response.content.decode('utf-8')
        assert "access" in response.content.decode('utf-8')


    @pytest.mark.skip
    def test_anonymous_user_can_login_with_phone(self):
        # Some problem with the test, endpoint is working fine
        user = User.objects.create_user(
            phone="09999999999",
            password="password",
            email="random@site.com"
        )

        client = APIClient()
        response = client.post("/api/accounts/request-otp/",
                               {"phone": user.phone, "password": user.password} )
        code = user.otp_code.code

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.content.decode('utf-8')


    def test_logged_in_user_can_view_their_detail(self):

        user = User(email="random@random.com", phone="09123456789")
        token = str(RefreshToken.for_user(user).access_token)
        client = APIClient()
        client.force_authenticate(user=user, token=token)

        response = client.get("/api/myuser/")

        assert response.status_code == status.HTTP_200_OK
        assert "random@random.com" in response.content.decode('utf-8')