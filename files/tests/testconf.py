
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from files.models import Folder

User = get_user_model()


# ----------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------

@pytest.fixture
def user():
    return User.objects.create_user(
        email="ali@test.com",
        phone="09123456789",
        password="password123",
    )


@pytest.fixture
def another_user():
    return User.objects.create_user(
        email="other@test.com",
        phone="09999999999",
        password="password123",
    )


# ----------------------------------------------------------------------
# Folder hierarchy
# ----------------------------------------------------------------------

@pytest.fixture
def root_folder(user):
    return Folder.get_or_create_folder("root", user, None)


@pytest.fixture
def documents_folder(user, root_folder):
    return Folder.create(
        name="Documents",
        user=user,
        parent_folder=root_folder,
    )


@pytest.fixture
def images_folder(user, root_folder):
    return Folder.create(
        name="Images",
        user=user,
        parent_folder=root_folder,
    )


# ----------------------------------------------------------------------
# API Client
# ----------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client