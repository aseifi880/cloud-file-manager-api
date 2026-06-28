import pytest
from django.db.models import QuerySet

from files.models import Folder, File

from files.tests.helpers import (
    uploaded_file,
    folder_exists,
    get_folder,
    get_child_folder,
    file_exists,
    file_path_exists,
    folder_path_exists,
)

from files.tests.testconf import user, root_folder

pytestmark = pytest.mark.django_db

@pytestmark
def test_upload_single_file_into_root(user, root_folder):

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("hello.txt")
        ],
        relative_paths=[
            "hello.txt"
        ],
    )

    assert File.objects.count() == 1

    uploaded = File.objects.first()

    assert uploaded.folder == root_folder
    assert uploaded.name == "hello.txt"
    assert file_path_exists(uploaded)


@pytestmark
def test_nested_directories_are_created(user, root_folder):

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("main.py")
        ],
        relative_paths=[
            "Project/src/main.py"
        ],
    )

    assert folder_exists(
        name="Project",
        user=user,
        parent=root_folder,
    )

    project = get_folder(
        name="Project",
        user=user,
        parent=root_folder,
    )

    assert folder_exists(
        name="src",
        user=user,
        parent=project,
    )

    src = get_child_folder(project, "src")

    assert folder_path_exists(project, user)
    assert folder_path_exists(src, user)

    assert file_exists(
        name="main.py",
        folder=src,
    )


@pytestmark
def test_multiple_files_create_complete_tree(user, root_folder):

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("main.py"),
            uploaded_file("utils.py"),
            uploaded_file("readme.md"),
        ],
        relative_paths=[
            "Project/src/main.py",
            "Project/src/utils.py",
            "Project/docs/readme.md",
        ],
    )

    assert File.objects.count() == 3

    project = get_folder(
        name="Project",
        user=user,
        parent=root_folder,
    )

    src = get_child_folder(project, "src")
    docs = get_child_folder(project, "docs")

    assert File.objects.filter(folder=src).count() == 2
    assert File.objects.filter(folder=docs).count() == 1


@pytestmark
def test_existing_folder_is_reused(user, root_folder):

    project = Folder.create(
        name="Project",
        user=user,
        parent_folder=root_folder,
    )

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("main.py")
        ],
        relative_paths=[
            "Project/main.py"
        ],
    )

    assert Folder.objects.filter(
        name="Project",
        parent=root_folder,
        user=user,
    ).count() == 1

    uploaded = File.objects.get()

    assert uploaded.folder == project

@pytestmark
def test_shared_directories_created_once(user, root_folder):

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("main.py"),
            uploaded_file("utils.py"),
            uploaded_file("config.py"),
        ],
        relative_paths=[
            "Project/src/main.py",
            "Project/src/utils.py",
            "Project/src/config.py",
        ],
    )

    project = get_folder(
        name="Project",
        user=user,
        parent=root_folder,
    )

    assert Folder.objects.filter(
        parent=project,
        name="src",
        user=user,
    ).count() == 1

@pytestmark
def test_upload_to_existing_nested_directory(user, root_folder):

    project = Folder.create(
        name="Project",
        user=user,
        parent_folder=root_folder,
    )

    src = Folder.create(
        name="src",
        user=user,
        parent_folder=project,
    )

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("app.py")
        ],
        relative_paths=[
            "Project/src/app.py"
        ],
    )

    uploaded = File.objects.get()

    assert uploaded.folder == src

@pytestmark
def test_empty_upload(user, root_folder):

    uploaded = Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[],
        relative_paths=[],
    )

    assert uploaded == []
    assert Folder.objects.count() == 1
    assert File.objects.count() == 0


@pytestmark
def test_file_path_count_mismatch_raises(user, root_folder):

    with pytest.raises(ValueError):

        Folder.upload_directory(
            user=user,
            parent_folder=root_folder,
            uploaded_files=[
                uploaded_file("hello.txt")
            ],
            relative_paths=[],
        )

@pytestmark
def test_files_are_uploaded_into_correct_folders(user, root_folder):

    Folder.upload_directory(
        user=user,
        parent_folder=root_folder,
        uploaded_files=[
            uploaded_file("a.py"),
            uploaded_file("b.py"),
        ],
        relative_paths=[
            "Project/src/a.py",
            "Project/docs/b.py",
        ],
    )

    project = get_folder(
        name="Project",
        user=user,
        parent=root_folder,
    )

    src = get_child_folder(project, "src")
    docs = get_child_folder(project, "docs")

    assert file_exists(
        name="a.py",
        folder=src,
    )

    assert file_exists(
        name="b.py",
        folder=docs,
    )