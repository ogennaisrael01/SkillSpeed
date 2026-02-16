import pytest
import factory
import random

from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestChildProfile:
    def test_child_onboard(self, guardian_client: APIClient):
        request_path = "/api/v1/profile/child/onboard/"

        request_data = {
            "date_of_birth": "2012-03-03",
            "first_name": str(factory.Faker("name")),
            "last_name": str(factory.Faker("name")),
            "middle_name": str(factory.Faker("name")),
            "gender": random.choice(["MALE", "FEMALE", "OTHER"])
        }

        response = guardian_client.post(path=request_path,
                                        data=request_data,
                                        format="json"
                                    )
        result = response.json()
        assert result["status"] == 'success'
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_fetch_child_profile(self, instructor_client: APIClient, child_profile):
        request_path = f"/api/v1/child/{child_profile.pk}/profile/"

        response = instructor_client.get(path=request_path)
        result = response.json()
        assert result["child_id"] == str(child_profile.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_child_profile_update_wrong_user(self, instructor_client: APIClient, child_profile):
        request_path = f"/api/v1/child/{child_profile.pk}/profile/"
        request_data = {
            "date_of_birth": "2019-03-02"
        }
        response = instructor_client.put(path=request_path)
        result = response.json()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_child_profile_update_guardian(self, guardian_client: APIClient, child_profile):
        request_path = f"/api/v1/child/{child_profile.pk}/profile/"
        request_data = {
            "date_of_birth": "2019-03-02"
        }
        response = guardian_client.put(path=request_path, 
                                       data=request_data, 
                                       format="json")
        result = response.json()
        print(result)
