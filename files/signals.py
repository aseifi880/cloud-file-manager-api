from pathlib import Path

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from files.models import Folder, File

user = get_user_model()
@receiver(post_save, sender=user)
def create_root_folder(sender, instance, created, **kwargs):
    if created  :
        Folder.objects.create(user=instance, name="root", parent=None)
