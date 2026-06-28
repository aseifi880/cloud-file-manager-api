import os.path
from pathlib import Path, PurePosixPath

from django.contrib.auth import get_user_model
from django.db import models, transaction

from core.base_model import BaseModel
from core.settings import BASE_DIR, MEDIA_ROOT


User = get_user_model()

def get_folder_path(instance: 'Folder', user: 'User'):
    os_friendly_email_address = user.email.replace('@', '_at_')
    base_path = Path(BASE_DIR / MEDIA_ROOT / "files" / os_friendly_email_address)

    path_parts = []
    current = instance
    while current:
        path_parts.append(current.name)
        current = current.parent
    path_parts.reverse()
    return base_path / '/'.join(path_parts)

def get_file_path(instance: 'File', filename: str):
    user = instance.user
    os_friendly_email_address = user.email.replace('@', '_at_')
    base_path: str = os.path.join("files", os_friendly_email_address)
    immediate_folder = instance.folder
    if immediate_folder.parent is None:
        return os.path.join(base_path, immediate_folder.name, filename.replace(' ', '_'))
    parent_folder: Folder = immediate_folder.parent
    path = os.path.join(parent_folder.name, instance.folder.name)
    while parent_folder.parent:
        parent_folder = parent_folder.parent
        path = os.path.join(parent_folder.name, path)
    return os.path.join(base_path, path, filename.replace(' ', '_'))




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

    @classmethod
    def get_or_create_folder(cls, name, user, parent_folder: "Folder | None"):
        folder = cls.objects.filter(
            name=name,
            user=user,
            parent=parent_folder,
            is_deleted=False,
        ).first()

        if folder:
            return folder

        return cls.create(
            name=name,
            user=user,
            parent_folder=parent_folder,
        )

    @classmethod
    @transaction.atomic
    def upload_directory(
        cls,
        user,
        parent_folder,
        uploaded_files,
        relative_paths,
    ):

        if len(uploaded_files) != len(relative_paths):
            raise ValueError("Files and paths count mismatch.")

        folder_cache = {}

        created_files = []

        for uploaded_file, relative_path in zip(uploaded_files, relative_paths):

            current_folder = parent_folder

            path = PurePosixPath(relative_path)

            current_path = ""

            # everything except filename
            for folder_name in path.parts[:-1]:

                current_path += "/" + folder_name

                if current_path in folder_cache:
                    current_folder = folder_cache[current_path]
                    continue

                folder, _ = Folder.objects.get_or_create(
                    name=folder_name,
                    user=user,
                    parent=current_folder,
                    defaults={
                        "user": user,
                        "parent": current_folder,
                    },
                )

                # make sure directory exists
                folder_path = get_folder_path(folder, user)
                Path(folder_path).mkdir(parents=True, exist_ok=True)

                folder_cache[current_path] = folder

                current_folder = folder

            file = File.create(
                user=user,
                file=uploaded_file,
                folder=current_folder,
                size=uploaded_file.size,
            )

            created_files.append(file)

        return created_files


    class Meta:
        unique_together = ('name', 'user', 'parent', 'is_deleted', 'deleted_at')



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