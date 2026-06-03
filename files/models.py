import os.path
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import models, transaction

from core import settings
from core.base_model import BaseModel
from core.settings import BASE_DIR, MEDIA_ROOT


User = get_user_model()

def get_folder_path(instance: 'Folder', user: 'User'):
    """

    :param instance: an instance of folder object
    :param user: the user to which the folder belongs to
    :return: returns the absolute path of instance which will be created using Path.mkdir
    """
    parent = instance.parent
    os_friendly_email_address = user.email.replace('@', '_at_')
    folder_path = Path(BASE_DIR / MEDIA_ROOT / "files" / os_friendly_email_address)
    path = os.path.join(parent.name, instance.name) if parent else instance.name
    while parent.parent:
        parent = parent.parent
        path = os.path.join(parent.name, path)
    return folder_path / path

def get_file_path(instance: 'File', filename: str):
    user = instance.user
    parent = instance.folder.parent
    os_friendly_email_address = user.email.replace('@', '_at_')
    folder_path = os.path.join( "files", os_friendly_email_address)
    path = os.path.join(parent.name, instance.folder.name) if parent else instance.folder.name
    while parent.parent:
        parent = parent.parent
        path = os.path.join(parent.name, path)
    return os.path.join(folder_path, path, filename.replace(' ', '_'))




# Create your models here.
class Folder(BaseModel):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name="children", null=True)


    def __str__(self):
        return f"{self.user} - {self.name}"

    @classmethod
    def create(cls, name, user, parent_folder) -> 'Folder':
        with transaction.atomic():
            folder = cls.objects.create(
                name=name,
                user=user,
                parent=parent_folder,
            )
            path = get_folder_path(folder, user)
            Path(path).mkdir(parents=True, exist_ok=True)
            return folder

    class Meta:
        unique_together = ('name', 'user', 'parent', 'is_deleted')


class File(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=get_file_path)
    size = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.folder is None:
            self.folder = Folder.objects.get(user=self.user, name="root")
        if self.name == "" or self.name is None:
            self.name = self.file.name
        super().save(*args, **kwargs)

    @classmethod
    def create(cls, user, file, size, folder) -> 'File':
        with transaction.atomic():
            file = cls.objects.create(
                user=user,
                file=file,
                folder=folder,
                size=size,
            )
            return file
    def __str__(self):
        return self.name if self.name else self.file.name

    class Meta:
        unique_together = ('name', 'folder', 'file', 'is_deleted')