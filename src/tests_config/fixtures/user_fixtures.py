from tests_config.factories import UserFactory

import pytest

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
def admin_user(db):
    return UserFactory(email="admin_user@gmail.com", is_active=True, \
                       is_verified=True, is_superuser=True, is_staff=True)