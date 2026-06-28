import pytest

from django.urls import reverse

from rest_framework import status

from files.models import Folder, File
from files.tests.helpers import (
    uploaded_file,
    directory_upload_payload,
)
from files.tests.testconf import user, root_folder, authenticated_client, api_client

pytestmark = pytest.mark.django_db


URL = reverse("upload-directory")

@pytestmark
def test_upload_directory_requires_authentication(api_client, root_folder):

    response = api_client.post(
        URL,
        {},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytestmark
def test_upload_directory_success(authenticated_client, root_folder):

    payload = directory_upload_payload(
        parent_folder=root_folder.pk,
        paths=[
            "Project/src/main.py",
            "Project/readme.md",
        ],
        files=[
            uploaded_file("main.py"),
            uploaded_file("readme.md"),
        ],
    )

    response = authenticated_client.post(
        URL,
        data=payload,
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["uploaded"] == 2

    assert File.objects.count() == 2

    assert Folder.objects.filter(name="Project").exists()

@pytestmark
def test_upload_directory_rejects_invalid_request(
    authenticated_client,
    root_folder,
):

    payload = {
        "parent_folder": root_folder.pk,
        "paths": [],
        "files": [
            uploaded_file("main.py"),
        ],
    }

    response = authenticated_client.post(
        URL,
        data=payload,
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytestmark
def test_upload_directory_missing_parent_folder(
    authenticated_client,
):

    payload = {
        "paths": [
            "main.py",
        ],
        "files": [
            uploaded_file("main.py"),
        ],
    }

    response = authenticated_client.post(
        URL,
        data=payload,
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytestmark
def test_upload_directory_returns_uploaded_count(
    authenticated_client,
    root_folder,
):

    payload = directory_upload_payload(
        parent_folder=root_folder.pk,
        paths=[
            "a.txt",
            "b.txt",
            "c.txt",
        ],
        files=[
            uploaded_file("a.txt"),
            uploaded_file("b.txt"),
            uploaded_file("c.txt"),
        ],
    )

    response = authenticated_client.post(
        URL,
        data=payload,
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert response.data == {
        "uploaded": 3
    }