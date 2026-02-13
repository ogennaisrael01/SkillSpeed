from rest_framework.test import APIClient
from rest_framework import status

from test.fixtures_config import (user, authenticated_client, api_client, 
                                  guardian_user, guardian, instructor_user,
                                  instructor, guardian_client, instructor_client
)
from ..profiles.models import Guardian, Instructor

import pytest

@pytest.mark.django_db
class TestUsers:
    def test_onboard(self, authenticated_client: APIClient):
        onboard_path = "/api/v1/profile/onboard/"
        request_data = {
            "role": "GUARDIAN",
            "profile_completes": True
        }
        response = authenticated_client.patch(path=onboard_path, data=request_data)
        result = response.json()
        assert result['status'] == "success"
        assert response.status_code == status.HTTP_200_OK

    def test_profile_mine_read_guardian(self, guardian_client, guardian):
        profile_path = "/api/v1/profile/me/"
        response = guardian_client.get(path=profile_path)
        result = response.json()
        assert str(guardian.pk) == result["detail"]['guardian_id']
        assert response.status_code == status.HTTP_200_OK


    def test_profile_mine_read_instructor(self, instructor_client: APIClient, instructor):
        profile_path = '/api/v1/profile/me/'
        response = instructor_client.get(path=profile_path)
        result = response.json()
        assert str(instructor.pk) == result["detail"]["instructor_id"]
        assert response.status_code == status.HTTP_200_OK
    
    def test_profile_public_instructor(self, instructor_client, guardian):
        """
        Docstring for test_profile_public
        
        :param self: Instructor user fetching the guardian profile
        :param instructor_client: Description
        :param guardian: Description
        """
        user_id = guardian.pk
        public_path = f"/api/v1/profile/{user_id}/"
        response = instructor_client.get(path=public_path)
        result = response.json()
        print("instructor test", result)
        assert user_id == result['detail']['guardian_id']
        assert response.status_code == status.HTTP_200_OK

    def test_profile_public_guardain(self, guardian_client, instructor):
        """
        Docstring for test_profile_public
        
        :param self: Guardian user fetching the instructor profile
        :param instructor_client: Description
        :param guardian: Description
        """
        user_id = instructor.pk
        public_path = f"/api/v1/profile/{user_id}/"
        response = guardian_client.get(path=public_path)
        result = response.json()
        print("guardian test", result)
        assert user_id == result['detail']['instructor_id']
        assert response.status_code == status.HTTP_200_OK


