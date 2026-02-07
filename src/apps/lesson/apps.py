from django.apps import AppConfig


class LessonConfig(AppConfig):
    name = 'apps.lesson'
    label = "lesson_app"
     
    def ready(self):
        from . import signals