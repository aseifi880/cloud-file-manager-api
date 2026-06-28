from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile

from files.models import Folder, File

def uploaded_file(
    filename: str,
    content: str = "Hello World!",
    content_type: str = "text/plain",
):

    return SimpleUploadedFile(
        name=filename,
        content=content.encode(),
        content_type=content_type,
    )


def directory_upload_payload(
    parent_folder,
    paths,
    files,
):

    return {
        "parent_folder": parent_folder,
        "paths": paths,
        "files": files,
    }


def folder_exists(
    name,
    user,
    parent=None,
):

    return Folder.objects.filter(
        name=name,
        user=user,
        parent=parent,
    ).exists()


def get_folder(
    name,
    user,
    parent=None,
):

    return Folder.objects.get(
        name=name,
        user=user,
        parent=parent,
    )


def file_exists(
    name,
    folder,
):

    return File.objects.filter(
        name=name,
        folder=folder,
    ).exists()


def get_file(
    name,
    folder,
):

    return File.objects.get(
        name=name,
        folder=folder,
    )

def folder_path_exists(folder, user):

    from files.models import get_folder_path

    return Path(get_folder_path(folder, user)).exists()


def file_path_exists(file):

    return Path(file.file.path).exists()


def get_child_folder(parent, name):

    return Folder.objects.get(
        parent=parent,
        name=name,
        user=parent.user,
    )