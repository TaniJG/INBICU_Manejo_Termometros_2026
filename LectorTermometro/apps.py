from django.apps import AppConfig


class LectortermometroConfig(AppConfig):
    name = 'LectorTermometro'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        pass

