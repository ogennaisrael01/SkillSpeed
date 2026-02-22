
from ..models import OneTimePassword, PasswordReset

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

import pytest
from uuid import UUID


@pytest.mark.api
@pytest.mark.django_db
class TestAuth:

    def test_registrations(self, api_client: APIClient,
                           setup_celery_test_config):
        registration_path = "/api/v1/auth/register/"
        request_data = {
            "email": "testemail@gmail.com",
            "first_name": "test_user",
            "last_name": "test_user_last",
            "password": "secure_password",
            "confirm_password": "secure_password"
        }
        response = api_client.post(path=registration_path, data=request_data)
        result = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        assert result.get("status") == "success"

    def test_login(self, api_client: APIClient, user):
        login_path = "/api/v1/auth/token/obtain/"
        request_data = {"email": user.email, "password": "secure_password"}
        response = api_client.post(path=login_path, data=request_data)
        result = response.json()
        user_id = result.get("user_data")["user_id"]
        assert response.status_code == status.HTTP_200_OK
        assert user_id is not None

    def test_account_verification(self, api_client: APIClient,
                                  user_verification):
        verification_path = "/api/v1/auth/verify/"
        otp_instance = OneTimePassword.objects.get(user=user_verification,
                                                   is_active=True)
        email = user_verification.email
        request_data = {"email": email, "code": otp_instance.raw_code}
        response = api_client.post(path=verification_path, data=request_data)
        result = response.json()
        assert result["status"] == "success"
        assert response.status_code == status.HTTP_200_OK

    def test_resend_otp(self, api_client: APIClient, user):
        resend_path = "/api/v1/auth/code/resend/"
        request_data = {"email": user.email}

        response = api_client.post(path=resend_path, data=request_data)
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert result.get("status") == "success"

    def test_password_reset(self, api_client: APIClient, user):
        # settings.CELERY_TASK_ALWAYS_EAGER = True
        email = user.email
        password_reset_path = "/api/v1/auth/password/reset/"
        request_data = {"email": email}
        response = api_client.post(path=password_reset_path, data=request_data)

        result = response.json()
        assert result.get("status") == "success"
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_code(self, api_client: APIClient, user,
                                         password_reset):
        confirm_path = "/api/v1/auth/password/reset/confirm/"
        password_reset.user = user
        password = PasswordReset.objects.get(user__email=user.email,
                                             is_active=True)
        request_data = {
            "code": password.raw_code,
            "password": "secure_password30",
            "confirm_password": "secure_password30"
        }
        response = api_client.post(path=confirm_path, data=request_data)
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert result["status"] == "success"

    def test_logout(self, authenticated_client, user):
        logout_path = "/api/v1/auth/logout/"
        token = RefreshToken.for_user(user)
        request_data = {"refresh_token": str(token)}
        response = authenticated_client.post(path=logout_path,
                                             data=request_data)
        result = response.json()
        assert result["status"] == "success"
        assert response.status_code == status.HTTP_200_OK
