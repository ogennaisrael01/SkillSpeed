from ..serializers import UserRegistrationSerializer

import pytest

from django.contrib.auth import get_user_model

UserModel = get_user_model()

@pytest.mark.django_db
class TestUserSerializer:
    def test_user_create(self):
        data = {
            "email": "testemail@gmail.com",
            "first_name": "test_user",
            "last_name": "test_user_last",
            "password": "secure_password",
            "confirm_password": "secure_password"
        }
        serializer = UserRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        assert isinstance(result, UserModel)
        assert result.email == data["email"]

