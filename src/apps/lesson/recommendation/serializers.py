from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound

from django.utils.translation import gettext_lazy as _
from django.db import transaction 

from .models import Recommendation, Skills
from ...skills.helpers import _child_age_or_none
from .services.recommendation_service import AgeRecommendation, AIRecommendation
from ...skills.serializers import SkillReadSerializer

class RecommendationSerializer(serializers.ModelSerializer):
    choices = ["system", "ai"]

    class Meta:
        model = Recommendation
        fields = [
            "recommendation_type"
        ]
    default_error_messages = {
        "invalid_choices": _("Please provide and accurate choice field")
    }

    def validate_recommendation_choices(self, value):
        if value.lower() not in self.choices:
            self.fail("invalid_choices")
        return value.upper()
    
    def create(self, validated_data):
        request = self.context.get("request")
        child_profile = self.context.get("child_profile")

        if request.user.active_account != child_profile:
            raise PermissionDenied()
        recommendation_choices = validated_data.get("recommendation_type")
        if recommendation_choices is None:
            raise serializers.ValidationError(_("Choices cannot be empty"))
         
        child_age = _child_age_or_none(child_profile)
        if child_age is None:
            raise serializers.ValidationError(_("Date of birth not provided. Please provide your date or choose interest to continue"))
            
        if recommendation_choices.lower() == self.choices[0]:
            recommendation = AgeRecommendation(child_age)
            response = recommendation.recommend()
            if response is None:
                raise NotFound()
            try:
                with transaction.atomic():
                    recommendation_table = Recommendation.objects.create(
                            child_profile=child_profile,
                            recommendation_score=1.0,
                            reason="Age-based recommendation",
                            recommendation_type="age",
                            recommended_by=Recommendation.RecommendedBy.SYSTEM     
                        )
                    recommendation_table.skills.set(response)
            except Exception as e:
                raise serializers.ValidationError("Error creating recommendation", code="invalid_request")
        elif recommendation_choices.lower() == self.choices[1]:
            list_of_child_interest = list()
            child_interest = child_profile.interest.all()
            for interest in child_interest:
                list_of_child_interest.append(interest.name)

            recommendation = AIRecommendation(list_of_child_interest, child_age)
            response = recommendation.recommend()
            for i in range(len(response)):
                title = response[i].get("title")
                category = response[i].get("category")
                difficulty = response[i].get("difficulty")
                similar_skills = Skills.objects.filter(name__icontains=title, 
                                                           category__name__icontains=category, 
                                                           skill_difficulty__icontains=difficulty, is_active=True)
                
                if similar_skills is None:
                    raise NotFound()
                try:
                    with transaction.atomic():
                        recommendation_table = Recommendation.objects.create(
                            child_profile=child_profile,
                            recommendation_score=response[i].get("score"),
                            category=category,
                            difficulty=difficulty,
                            reason=response[i].get("guardian_reason"),
                            recommendation_type=response[i].get("recommendation_basis"),
                            recommended_by=Recommendation.RecommendedBy.AI         
                            )
                        recommendation_table.skills.set(similar_skills)
                except Exception as e:
                    raise serializers.ValidationError(_(f"Error occurred when trying to send recommendation: {str(e)}"))
        return response
    

class RecommendationReadSerializer(serializers.ModelSerializer):
    skills = SkillReadSerializer(many=True, read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "recommendation_id", "skills",
            "recommendation_score", "category",
            "difficulty", "reason", "recommended_by",
            "created_at", "recommendation_type"
        ]