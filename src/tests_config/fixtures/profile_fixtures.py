from tests_config.factories import (
    InstructorFactory, 
    GuardianFactory,
    ChildProfileFactory
)

import pytest

@pytest.fixture
def guardian(db, guardian_user):
    return GuardianFactory(user=guardian_user)

@pytest.fixture
def instructor(db, instructor_user):
    return InstructorFactory(user=instructor_user)


@pytest.fixture
def child_profile(db, guardian_user):
    return ChildProfileFactory(guardian=guardian_user)