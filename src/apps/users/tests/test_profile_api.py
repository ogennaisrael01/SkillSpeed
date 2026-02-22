from rest_framework.test import APIClient
from rest_framework import status

import pytest
from typing import Any


@pytest.mark.django_db
class TestUsers:

    def test_onboard(self, authenticated_client: APIClient):
        onboard_path = "/api/v1/profile/onboard/"
        request_data = {"role": "GUARDIAN", "profile_completes": True}
        response = authenticated_client.patch(path=onboard_path,
                                              data=request_data)
        result = response.json()
        assert result['status'] == "success"
        assert response.status_code == status.HTTP_200_OK

    def test_profile_mine_read_guardian(self, guardian_client, guardian):
        profile_path = "/api/v1/profile/detail/"
        response = guardian_client.get(path=profile_path)
        result = response.json()
        assert str(guardian.pk) == result["detail"]['guardian_id']
        assert response.status_code == status.HTTP_200_OK

    def test_profile_mine_read_instructor(self, instructor_client: APIClient,
                                          instructor):
        """ Test instructor profile (read view)"""
        profile_path = '/api/v1/profile/detail/'
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
        assert str(user_id) == result['detail']['guardian_id']
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
        assert str(user_id) == result['detail']['instructor_id']
        assert response.status_code == status.HTTP_200_OK

    def test_profile_view_admin(self, admin_client: APIClient, admin_user: Any,
                                guardian, instructor):
        """ Retrieve user profiles """
        profile_path = "/api/v1/profile/"
        response = admin_client.get(path=profile_path)
        result = response.json()
        assert result["status"] == "success"
        assert "guardian_data" and "instructor_data" in result
        assert response.status_code == status.HTTP_200_OK

    def test_profile_patch_instructor(self, instructor_client: APIClient,
                                      instructor, create_certificate):

        update_path = "/api/v1/profile/detail/"
        request_data = {
            "display_name":
            "Test Instructor",
            "certificates": [{
                "name": create_certificate.name,
                "issued_on": "2025-03-02",
                "description": "certificate description"
            }]
        }
        response = instructor_client.put(path=update_path,
                                         data=request_data,
                                         format="json")
        result: dict = response.json()
        assert result["instructor_id"] == str(instructor.pk)
        assert result["display_name"] == request_data["display_name"]
        assert response.status_code == status.HTTP_200_OK

    def test_profile_patch_guardian(self, guardian_client: APIClient,
                                    guardian):
        update_path = "/api/v1/profile/detail/"

        request_data = {"display_name": "Test Guardian"}
        response = guardian_client.put(path=update_path,
                                       data=request_data,
                                       format="json")
        result = response.json()
        assert result["display_name"] == request_data["display_name"]
        assert result["guardian_id"] == str(guardian.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_role_switch(self, guardian_client: APIClient):
        """ 
        guardian can switch from their acctive profile as guardian to child 
        so they can be able to access child content
        """
        url_path = "/api/v1/profile/switch/"
        request_data = {"role": "CHILD"}
        response = guardian_client.patch(path=url_path,
                                         data=request_data,
                                         format="json")
        result = response.json()
        assert result["status"] == "success"
        assert response.status_code == status.HTTP_200_OK
