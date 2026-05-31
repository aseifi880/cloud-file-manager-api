from celery import shared_task
from django.core.files.storage import default_storage
from django.db import transaction

from files.models import File, Folder


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
        # Hard delete the database record (optional)
        file_obj.delete()
        return f"File {file_id} permanently deleted."
    except File.DoesNotExist:
        return f"File {file_id} not found or already deleted."

@shared_task
def permanent_delete_folder(folder_id):
    """
    Recursively delete all physical files inside a folder and its subfolders,
    then hard‑delete the folder and its descendant records.
    """
    try:
        folder = Folder.all_objects.get(id=folder_id, is_deleted=True)
        _delete_folder_files_recursive(folder)
        # Hard delete the folder (cascade will delete children because of on_delete=CASCADE)
        folder.delete()
        return f"Folder {folder_id} and its contents permanently deleted."
    except Folder.DoesNotExist:
        return f"Folder {folder_id} not found or already deleted."

def _delete_folder_files_recursive(folder):
    """Helper: delete physical files in this folder and all subfolders."""
    # Delete files directly in this folder
    for file_obj in folder.files.all():  # files already filtered by ActiveManager? Use all_objects to include deleted
        if file_obj.file and default_storage.exists(file_obj.file.name):
            default_storage.delete(file_obj.file.name)
    # Recurse into child folders (including soft‑deleted ones)
    for child in folder.children.all():
        _delete_folder_files_recursive(child)