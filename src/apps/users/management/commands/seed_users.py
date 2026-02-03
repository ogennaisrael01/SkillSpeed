from django.core.management import BaseCommand
from django.contrib.auth import get_user_model

from faker import Faker
import random

class Command(BaseCommand):
    help = "create users"
    User = get_user_model()
    faker = Faker()


    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Tasks..."))
        roles = getattr(self.User.UserRoles, "choices")
        for _ in range(50):
            self.User.objects.create_user(email=self.faker.email(safe=True),
                                          first_name=self.faker.file_name(), last_name=self.faker.last_name(),
                                          password=self.faker.password(length=6), is_active=True, is_verified=True,
                                          user_role=(role[0] for role in roles))
            
        self.stdout.write(self.style.SUCCESS("SuccessFully Populated user table"))