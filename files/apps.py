from django.apps import AppConfig
from django.db.models.signals import post_save



class FilesConfig(AppConfig):
    name = 'files'

    def ready(self):
        import files.signals