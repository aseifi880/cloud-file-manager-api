from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'phone','first_name',
                    'last_name', 'is_staff', 'is_active',
                    'date_joined',
                    )
