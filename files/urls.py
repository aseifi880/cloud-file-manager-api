from django.urls import path

from files.views import FolderListView, UploadFile, AddFolder, DeleteFolder, DeleteFile, DownloadFile, FileLink, \
    FileSearchView

urlpatterns = [
    path('myfolders/', FolderListView.as_view(), name='folder-list'),
    path('add-file/', UploadFile.as_view(), name='add-file'),
    path('add-folder/', AddFolder.as_view(), name='add-folder'),
    path('delete-file/<int:file_id>/', DeleteFile.as_view(), name='delete-file'),
    path('delete-folder/<int:folder_id>/', DeleteFolder.as_view(), name='delete-folder'),
    path('download-file/<int:file_id>/', DownloadFile.as_view(), name='download-file'), # gives a download link
    # returns an api response that contains the download link from above path
    path('myfiles/<int:file_id>/download/', FileLink.as_view(), name='download-link'),
    # append ?search=<keyword> for search
    path('myfiles/', FileSearchView.as_view(), name='myfiles-search'),
]