from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from ..models import OneTimePassword

import pytest


@pytest.mark.django_db
class TestModel:
    User = get_user_model()
    password = "secure_passwrd"
    email = "test_user@gmail.com"

    def test_customuser_model(self):
        user = self.User.objects.create_user(email=self.email,
                                             password=self.password)

        assert check_password(self.password, user.password)
        assert self.email == user.email
        assert OneTimePassword.objects.filter(user=user).exists()

    def test_admin_user(self):
        user = self.User.objects.create_superuser(email=self.email,
                                                  password=self.password)

        assert check_password(self.password, user.password)
        assert user.is_superuser and user.is_staff

    def test_guardian_model(self, guardian):
        expected_email = "guardianemail@gmail.com"
        assert expected_email == guardian.user.email
        assert guardian.user.user_role == self.User.UserRoles.GUARDIAN

    def test_instructor_model(self, instructor):
        expected_email = "instructoremail@gmail.com"
        assert expected_email == instructor.user.email
        assert instructor.user.user_role == self.User.UserRoles.INSTRUCTOR

    def test_child_profile_model(self, guardian_user, child_profile):
        expected_date_of_birth = '2014-02-10'
        assert child_profile.guardian == guardian_user
        assert child_profile.date_of_birth == expected_date_of_birth
