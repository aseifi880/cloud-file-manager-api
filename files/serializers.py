from django.db.models import Model
from rest_framework import serializers

from files.models import Folder, File


class FileSerializer(serializers.ModelSerializer):
    folder = serializers.StringRelatedField(read_only=True)
    file = serializers.FileField(read_only=True, use_url=True, )
    class Meta:
        model = File
        fields = ['id', 'name', 'folder','size', 'file','created_at']


class FolderSerializer(serializers.ModelSerializer):

    parent = serializers.StringRelatedField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'created_at']


class UploadFileSerializer(serializers.Serializer):
    file = serializers.FileField()

    def __init__(self, *args, **kwargs):
        super(UploadFileSerializer, self).__init__(*args, **kwargs)
        self.fields['folder'] = serializers.PrimaryKeyRelatedField(
            queryset=Folder.objects.filter(user=self._user),
            default=Folder.objects.get(user=self._user, name='root')
        )

    def validate_file(self, file):
        user = self.context.get('request').user

        # file size limitation
        max_upload_size = user.get_max_upload_size()
        if max_upload_size < file.size:
            max_size = max_upload_size // (1024 * 1024)
            err = "فایل ارسالی بزرک تر از مقدار مجاز است. حجم فایل باید کمتر از %s مگابایت باشد." % max_size

            raise serializers.ValidationError(err)

        # storage limitation
        storage_quota = user.get_storage_quota()
        storage_used = user.get_current_storage_usage()
        if storage_used + file.size > storage_quota:
            remaining = (storage_quota - storage_used) // 1024 ** 2
            err = "شما %s مگابایت حجم باقی مانده دارید. فایل ارسالی بزرگ تر از این مقدار است." % remaining
            raise serializers.ValidationError(err)

        return file
    @property
    def _user(self):
        request = self.context.get('request', None)
        if request:
            return request.user
        return None


class AddFolderSerializer(serializers.Serializer):
    name = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'] = serializers.PrimaryKeyRelatedField(
            queryset=Folder.objects.filter(user=self._user),
            default=Folder.objects.get(user=self._user, name='root')
        )

    @property
    def _user(self):
        request = self.context.get('request', None)
        if request:
            return request.user
        return None


class FolderListSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    files = FileSerializer(many=True, read_only=True)

    def get_children(self, obj):
        return FolderListSerializer(obj.children, many=True).data


    class Meta:
        model = Folder
        fields = ['id', 'name', 'children', 'files']


class FileDownloadSerializer(serializers.ModelSerializer):
    download_url = serializers.HyperlinkedIdentityField(
        view_name='download-file',
        lookup_field='id'
    )

    class Meta:
        model = File
        fields = ['id', 'name', 'size', 'file','download_url']

