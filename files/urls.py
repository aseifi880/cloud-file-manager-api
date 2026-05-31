from django.urls import path

from files.views import FolderListView, UploadFile, AddFolder, DeleteFolder, DeleteFile

urlpatterns = [
    path('myfiles/', FolderListView.as_view(), name='folder-list'),
    path('add-file/', UploadFile.as_view(), name='add-file'),
    path('add-folder/', AddFolder.as_view(), name='add-folder'),
    path('delete-file/<int:file_id>/', DeleteFile.as_view(), name='delete-file'),
    path('delete-folder/<int:folder_id>/', DeleteFolder.as_view(), name='delete-folder'),
]