from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import OneTimePassword, PasswordReset
from apps.users.helpers import _hash_otp_code
from test.helpers import password_reset_token
from apps.users.profiles.models import Guardian, Instructor

import factory

UserModel = get_user_model()
otp_code = "0987494"
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserModel
    
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    email = factory.LazyAttribute(lambda o: f"{o.first_name}@gmail.com")
    password = factory.PostGenerationMethodCall("set_password", "secure_password")
    is_active = True
    is_verified = True

class OneTimePasswordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OneTimePassword
    
    user = factory.SubFactory(UserFactory)
    hash_code = _hash_otp_code(code=otp_code)

class PasswordResetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PasswordReset
    
    reset_code = _hash_otp_code(code=otp_code)
    user = factory.SubFactory(UserFactory)
    raw_code = otp_code
    
class GuardianFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Guardian
    user = factory.SubFactory(UserFactory)
    display_name = factory.LazyAttribute(lambda guardian: f"{guardian.user.first_name} {guardian.user.last_name}")

class InstructorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Instructor
    user = factory.SubFactory(UserFactory)
    display_name  = factory.LazyAttribute(lambda instructor: f"{instructor.user.first_name} {instructor.user.last_name}")