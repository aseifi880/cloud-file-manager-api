import os
import shutil

from celery import shared_task
from django.core.files.storage import default_storage
from django.db import transaction

from files.models import File, Folder, get_folder_path


@shared_task
def permanent_delete_file(file_id):
    """
    Permanently delete a single file's physical storage and database record.
    """
    try:
        file_obj = File.all_objects.get(id=file_id, is_deleted=True)
        # Delete physical file
        if file_obj.file and default_storage.exists(file_obj.file.name):
            default_storage.delete(file_obj.file.name)
            print(f"Deleted file: {file_obj.file.name}")
        else:
            print(f"File not found on disk: {file_obj.file.name if file_obj.file else 'None'}")

        file_obj.delete()
        return f"File {file_id} permanently deleted."
    except File.DoesNotExist:
        return f"File {file_id} not found or already deleted."

@shared_task
def permanent_delete_folder(folder_id):
    """Permanently delete folder and all contents."""
    try:
        folder = Folder.all_objects.get(id=folder_id, is_deleted=True)
        user = folder.user
        path = get_folder_path(folder, user)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=False)

        with transaction.atomic():
            _delete_folder_files_recursive(folder)
            folder.delete()

        return f"Folder {folder_id} permanently deleted."

    except Folder.DoesNotExist:
        return f"Folder {folder_id} not found or already deleted."

def _delete_folder_files_recursive(folder):
    """Helper: delete physical files in this folder and all subfolders."""
    # Delete files directly in this folder
    for file_obj in folder.files.all():
        if file_obj.file and default_storage.exists(file_obj.file.name):
            default_storage.delete(file_obj.file.name)

    for child in folder.children.all():
        _delete_folder_files_recursive(child)