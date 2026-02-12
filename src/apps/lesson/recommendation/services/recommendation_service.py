from ....skills.models import Skills
from .prompts import build_prompt
from .generate_service import generate_recommendations

import logging

logger = logging.getLogger(__name__)

class AgeRecommendation:
    def __init__(self, child_age):
        self.child_age: int = child_age

    def optimize_queryset(self):
        queryset = Skills.objects.select_related("category", "user")
        return queryset.all()

    def recommend(self):
        queryset = self.optimize_queryset()

        # Get recommendation where the min_age > child_age or the max_age < child_age
        age_based_recommendation = queryset.filter(min_age__lte=self.child_age, 
                                                   max_age__gte=self.child_age, is_active=True, is_delete=False)

        return age_based_recommendation
    
class AIRecommendation:
    def __init__(self, interest = None, age: int = None):
        self.interest = interest
        self.age = age

    def recommend(self):
        if not isinstance(self.interest, list):
            raise TypeError("Not a valid instance required for processing request")
        prompts = build_prompt(age=self.age, interest=self.interest)
        response = generate_recommendations(prompt=prompts)
        logger.debug("AI RESPONSE:", response)
        return response