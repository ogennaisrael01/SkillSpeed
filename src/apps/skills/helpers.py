from ..users.profiles.models import ChildProfile

from django.utils import timezone

def _child_age_or_none(child_profile):
    if not isinstance(child_profile, ChildProfile):
        return None
    date_of_birth = getattr(child_profile, "date_of_birth", None)
    if date_of_birth is None:
        return None
    current_year = timezone.now().year
    child_birth_year = date_of_birth.year
    return current_year - child_birth_year

def _is_age_appropriate(skill, age):
    min_age = getattr(skill, "min_age", None)
    max_age = getattr(skill, "max_age", None)
    if min_age is not None and age < min_age:
        return False
    if max_age is not None and age > max_age:
        return False
    return True


    

    
    
