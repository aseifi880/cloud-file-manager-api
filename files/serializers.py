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