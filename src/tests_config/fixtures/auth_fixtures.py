from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

import pytest


@pytest.fixture
def api_client():
    return APIClient()

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

@pytest.fixture
def admin_client(db, api_client, admin_user):
    token = RefreshToken.for_user(user=admin_user)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return api_client
