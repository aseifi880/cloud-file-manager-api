from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.settings import BASE_DIR, MEDIA_ROOT
from files.models import Folder, File
from files.serializers import UploadFileSerializer, FolderListSerializer, AddFolderSerializer, FolderSerializer, \
    FileSerializer
from files.tasks import permanent_delete_folder, permanent_delete_file


# Create your views here.
class UploadFile(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UploadFileSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            file = File.create(
                user=request.user,
                file=serializer.validated_data['file'],
                folder=serializer.validated_data['folder'],
                size=request.FILES['file'].size
            )
            return Response(FileSerializer(file).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


class FolderListView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        folders = Folder.objects.filter(user=request.user, name='root').prefetch_related('children').all()
        serializer = FolderListSerializer(folders, many=True)
        return Response(serializer.data)


class AddFolder(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddFolderSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            folder = Folder.create(
                name=serializer.validated_data['name'],
                user=request.user,
                parent_folder=serializer.validated_data['parent'],
            )
            return Response(FolderSerializer(folder).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e),
            },status=status.HTTP_400_BAD_REQUEST)


class DeleteFile(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id):
        # Retrieve the file (using default manager to ensure it's not already deleted)
        file_obj = get_object_or_404(File, id=file_id, user=request.user, is_deleted=False)

        with transaction.atomic():
            # Soft delete the record
            file_obj.is_deleted = True
            file_obj.deleted_at = timezone.now()
            file_obj.save(update_fields=['is_deleted', 'deleted_at'])

            # Schedule permanent physical deletion after 48 hours (in seconds)
            permanent_delete_file.apply_async(args=[file_obj.id], countdown=48 * 3600)

        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteFolder(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, folder_id):
        folder = get_object_or_404(Folder, id=folder_id, user=request.user, is_deleted=False)

        # Protect root folder
        if folder.name == 'root' and folder.parent is None:
            return Response({'error': 'Cannot delete the root folder.'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Recursively soft‑delete all descendants
            _soft_delete_folder_tree(folder)

            # Schedule permanent physical cleanup of the entire tree after 48 hours
            permanent_delete_folder.apply_async(args=[folder.id], countdown=48 * 3600)

        return Response(status=status.HTTP_204_NO_CONTENT)

def _soft_delete_folder_tree(folder):
    """Recursively set is_deleted=True on a folder and all its children."""
    now = timezone.now()
    # Soft delete the folder itself
    folder.is_deleted = True
    folder.deleted_at = now
    folder.save(update_fields=['is_deleted', 'deleted_at'])

    # Soft delete all direct files
    folder.files.update(is_deleted=True, deleted_at=now)

    # Recurse into child folders
    for child in folder.children.all():
        _soft_delete_folder_tree(child)