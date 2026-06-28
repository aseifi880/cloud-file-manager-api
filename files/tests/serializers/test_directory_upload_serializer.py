import pytest

from rest_framework.test import APIRequestFactory

from files.models import Folder
from files.serializers import DirectoryUploadSerializer

from files.tests.helpers import uploaded_file
from files.tests.testconf import user, root_folder

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_factory():
    return APIRequestFactory()

@pytestmark
def test_serializer_is_valid(user, root_folder, request_factory):

    request = request_factory.post("/")

    request.user = user

    request.FILES.setlist(
        "files",
        [
            uploaded_file("main.py"),
            uploaded_file("readme.md"),
        ],
    )

    serializer = DirectoryUploadSerializer(
        data={
            "parent_folder": root_folder.pk,
            "paths": [
                "Project/src/main.py",
                "Project/readme.md",
            ],
        },
        context={
            "request": request,
        },
    )

    assert serializer.is_valid()

@pytestmark
def test_serializer_rejects_mismatched_lengths(
    user,
    root_folder,
    request_factory,
):

    request = request_factory.post("/")

    request.user = user

    request.FILES.setlist(
        "files",
        [
            uploaded_file("main.py"),
        ],
    )

    serializer = DirectoryUploadSerializer(
        data={
            "parent_folder": root_folder.pk,
            "paths": [],
        },
        context={
            "request": request,
        },
    )

    assert not serializer.is_valid()

    assert "non_field_errors" in serializer.errors

@pytestmark
def test_serializer_requires_parent_folder(
    user,
    request_factory,
):

    request = request_factory.post("/")

    request.user = user

    request.FILES.setlist(
        "files",
        [
            uploaded_file("main.py"),
        ],
    )

    serializer = DirectoryUploadSerializer(
        data={
            "paths": [
                "main.py",
            ]
        },
        context={
            "request": request,
        },
    )

    assert not serializer.is_valid()

    assert "parent_folder" in serializer.errors

@pytestmark
def test_serializer_save_creates_uploaded_files(
    user,
    root_folder,
    request_factory,
):

    request = request_factory.post("/")

    request.user = user

    request.FILES.setlist(
        "files",
        [
            uploaded_file("main.py"),
            uploaded_file("utils.py"),
        ],
    )

    serializer = DirectoryUploadSerializer(
        data={
            "parent_folder": root_folder.pk,
            "paths": [
                "Project/src/main.py",
                "Project/src/utils.py",
            ],
        },
        context={
            "request": request,
        },
    )

    assert serializer.is_valid()

    uploaded_files = serializer.save()

    assert len(uploaded_files) == 2

    assert Folder.objects.filter(name="Project").exists()