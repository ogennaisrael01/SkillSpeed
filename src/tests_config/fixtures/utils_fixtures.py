from tests_config.factories import (
    CertificateFactory, 
    OneTimePasswordFactory, 
    PasswordResetFactory
)

import pytest

@pytest.fixture(autouse=True)
def setup_celery_test_config(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

@pytest.fixture
def otp_code(db, user_verification):
    return OneTimePasswordFactory(user=user_verification)

@pytest.fixture
def password_reset(db, user):
    return PasswordResetFactory(user=user)

@pytest.fixture
def create_certificate(db, instructor):
    return CertificateFactory(user=instructor, name="Certificate Name")