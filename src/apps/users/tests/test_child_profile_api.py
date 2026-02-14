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
    