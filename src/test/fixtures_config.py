import pytest
from .factories.user_factory import (UserFactory, OneTimePasswordFactory, 
                                     PasswordResetFactory, GuardianFactory,
                                     InstructorFactory,
)

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def setup_celery_test_config(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture
def user(db):
    return UserFactory(email="test_useremial@gmail.com")

@pytest.fixture
def guardian_user(db):
    return UserFactory(email="guardianemail@gmail.com", user_role="GUARDIAN")

@pytest.fixture
def instructor_user(db):
    return UserFactory(email="instructoremail@gmail.com", user_role="INSTRUCTOR")

@pytest.fixture
def user_verification(db):
    return UserFactory(email="test_useremail@gmail.com",
           is_active=False,
           is_verified=False)

@pytest.fixture
def guardian(db, guardian_user):
    return GuardianFactory(user=guardian_user)

@pytest.fixture
def instructor(db, instructor_user):
    return InstructorFactory(user=instructor_user)


@pytest.fixture
def otp_code(db, user_verification):
    return OneTimePasswordFactory(user=user_verification)

@pytest.fixture
def password_reset(db, user):
    return PasswordResetFactory(user=user)

@pytest.fixture
def authenticated_client(api_client, user):
    token = RefreshToken.for_user(user=user)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return api_client

@pytest.fixture
def instructor_client(db, instructor_user):
    api_client = APIClient()
    token = RefreshToken.for_user(user=instructor_user)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return api_client

@pytest.fixture
def guardian_client(db, guardian_user):
    api_client = APIClient()
    token = RefreshToken.for_user(user=guardian_user)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return api_client