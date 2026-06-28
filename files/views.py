from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from files.filters import FileListFilter
from files.models import Folder, File
from files.serializers import UploadFileSerializer, FolderListSerializer, AddFolderSerializer, FolderSerializer, \
    FileSerializer, DirectoryUploadSerializer

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
        file_obj = get_object_or_404(File, id=file_id, user=request.user)

        with transaction.atomic():
            # Soft delete the record
            file_obj.is_deleted = True
            file_obj.deleted_at = timezone.now()
            file_obj.save(update_fields=['is_deleted', 'deleted_at'])

            # Schedule permanent physical deletion after 48 hours (in seconds)
            permanent_delete_file.apply_async(args=[file_obj.id], countdown=15)

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
            permanent_delete_folder.apply_async(args=[folder.id], countdown=15)

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


class DownloadFile(APIView):
    """
    this view is used to download a file. it isn't used directly in itslef
    rather used inside a serializer which is in turn used in the FileLink view
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file_obj = get_object_or_404(File, id=file_id, user=request.user)
        file_path = file_obj.file.path
        if not default_storage.exists(file_path):
            return Response({'error': 'فایل مورد نظر موجود نیست.'},
                            status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(
            open(file_path, 'rb', smart_str(file_obj.name)),
                as_attachment=True,
                filename=file_obj.file.name
        )
        response['Content-Type'] = file_obj.file.file.content_type or 'application/octet-stream'
        response['Content-Length'] = file_obj.file.size
        return response


class FileLink(APIView):
    """
    this view is used to return a json response containing the download link of the
    requested file along with other info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):

        file_obj = get_object_or_404(File, id=file_id, user=request.user)
        serializer = FileSerializer(file_obj, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class FileSearchView(ListAPIView):

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileListFilter
    serializer_class = FileSerializer

    def get_queryset(self):
        queryset = File.objects.select_related('folder').filter(user=self.request.user).all()
        return queryset


class DirectoryUploadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = DirectoryUploadSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        files = serializer.save()

        return Response(
            {
                "uploaded": len(files)
            },
            status=201,
        )