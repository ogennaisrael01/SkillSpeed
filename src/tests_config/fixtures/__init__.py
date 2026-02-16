
"""My Package for handiling all test imports """

__author__ = "Ogenna Israel"

from .auth_fixtures import (
    api_client, 
    instructor_client, 
    guardian_client, 
    authenticated_client, 
    admin_client
)
from .profile_fixtures import (
    guardian,
    instructor,
    child_profile
)

from .user_fixtures import (
    user, 
    guardian_user, 
    user_verification, 
    instructor_user,
    admin_user
)

from .utils_fixtures import (
    create_certificate   
)

__all__ = [
    "api_client",
    "instructor_client",
    "guardian_client",
    "authenticated_client",
    "admin_client",
    "guardian",
    "instructor",
    "user",
    "guardian_user",
    "user_verification",
    "instructor_user",
    "admin_user",
    "create_certificate",
    "child_profile"
]
