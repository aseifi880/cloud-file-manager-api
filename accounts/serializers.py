from rest_framework import serializers

from accounts.models import User


# region Auth
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    phone = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11, required=True)
    password = serializers.CharField(write_only=True, required=True)


class VerifyOTPSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)
    phone = serializers.CharField(max_length=11)


# endregion


class UserViewSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "is_superuser",
        )


class UserRetrieveViewSerializer(serializers.ModelSerializer):
    max_file_size_mb = serializers.SerializerMethodField()

    def get_max_file_size_mb(self, obj):
        return obj.get_max_file_size() / (1024 * 1024)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "max_file_size_mb",
        )
        read_only_fields = fields


class UserUpdateViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone")

