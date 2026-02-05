from django.core.management import BaseCommand
from django.contrib.auth import get_user_model

from ...models import SkillCategory, Skills

from faker import Faker
import random
import uuid

class Command(BaseCommand):
    help = "seed skills db.."
    faker = Faker()
    User = get_user_model()

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting task. Populating skills database.."))

        admin_user = self.User.objects.filter(is_superuser=True).first()
        categories = getattr(SkillCategory.Category, "choices")
        if any([admin_user, categories]) is None:
            self.stdout.write(self.style.WARNING("admin user and categories are required to populate skills"))

        for category in categories:
            if SkillCategory.objects.filter(name=category[0]).exists():
                continue
            SkillCategory.objects.get_or_create(user=admin_user, name=category[0], descriptions=self.faker.texts(nb_texts=200))
        self.stdout.write(self.style.SUCCESS("Successfully populated category table"))
        skill_category_instances = SkillCategory.objects.filter(is_active=True).all()
        instrutors = self.User.objects.filter(user_role="INSTRUCTOR")
        difficulty = getattr(Skills.SkillDifficulty, "choices")
        nm_of_skills = 5_000
        batch_size = 1_000

        skills = list()
        for i in range(nm_of_skills):
            instances = Skills(skill_id=uuid.uuid4(), category=random.choice(skill_category_instances), user=random.choice(instrutors),
                               name=self.faker.text(max_nb_chars=50), description=self.faker.text(max_nb_chars=100), skill_difficulty=random.choice(difficulty),
                               min_age=random.randint(5, 8), max_age=random.randint(8, 15), price=random.randint(1000, 10000),
                               is_paid=True)
            
            skills.append(instances)
            if len(skills) == batch_size:
                Skills.objects.bulk_create(skills)
                self.stdout.write(self.style.SUCCESS(f"Successfully populated {len(skills)}"))
                skills.clear()
        #if any left overs 
        if len(skills) > 0:
            Skills.objects.bulk_create(skills)
        self.stdout.write(self.style.SUCCESS("Successfully Populated skills table.."))
