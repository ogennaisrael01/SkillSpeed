from ..serializers import UserRegistrationSerializer
from ..profiles.serializers import ChildProfileCreateSerializer

from django.contrib.auth import get_user_model
from django.http import HttpRequest

import random
import pytest
from faker import Faker

UserModel = get_user_model()
faker = Faker()


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

    def test_child_onboard_serializer(self, guardian_user):
        request = HttpRequest
        request.user = guardian_user

        request_data = {
            "date_of_birth": "2012-01-02",
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "middle_name": faker.last_name(),
            "gender": random.choice(["MALE", "FEMALE", "OTHER"])
        }

        serializer = ChildProfileCreateSerializer(data=request_data,
                                                  context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        assert result.guardian == guardian_user
