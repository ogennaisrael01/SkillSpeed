from django.db import models

from ...users.profiles.models import ChildProfile
from ...skills.models import Skills

import uuid

class Recommendation(models.Model):

    class DifficultyLevel(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"
    
    class RecommendationType(models.TextChoices):
        AGE_BASED = "AGE_BASED", "Age Based"
        INTEREST_BASED = "INTEREST_BASED", "Interest Based"
        AI_BASED = "AI_BASED", "AI Based"   
        OTHER = "OTHER", "Other"
    
    class RecommendedBy(models.TextChoices):
        SYSTEM = "SYSTEM", "System"
        AI = "AI", "AI"

    recommendation_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, max_length=20, db_index=True)

    child_profile = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="recommendations")

    skills = models.ManyToManyField(Skills, related_name="skills")

    recommendation_score = models.FloatField(help_text="confidence with recomendation")

    category = models.CharField(max_length=200, null=True)

    difficulty = models.CharField(choices=DifficultyLevel.choices, default=None)
    
    reason = models.TextField(null=True, blank=True)

    recommendation_type = models.CharField(max_length=200, null=True, blank=True)
    recommended_by = models.CharField(max_length=200, null=True, choices=RecommendedBy.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
        constraints = [ # unique constraint to prevent duplicate recommendations for the same child profile based on the same skills
            models.UniqueConstraint(fields=['child_profile', 'recommenedation_type', 'category', 'difficulty'], name='unique_recommendation_per_child')
            
        ]
        
    def __str__(self):        
        return f"Recommendation for {self.child_profile} with score {self.recommendation_score}"

