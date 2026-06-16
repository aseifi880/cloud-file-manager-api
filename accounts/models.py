import random
from datetime import timedelta
from typing import Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.managers import CustomUserManager
from core.base_model import BaseModel


class Plan(BaseModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    display_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveBigIntegerField(default=0)
    max_upload_size = models.PositiveBigIntegerField(default=100*1024*1024)
    storage_quota = models.PositiveBigIntegerField(default=1024*1024*1024)

    def __str__(self):
        return self.name

def get_free_plan():
    plan, created = Plan.objects.get_or_create(name="free")
    if created:
        plan.max_upload_size = 10 * 1024 * 1024
        plan.storage_quota = 1024 * 1024 * 1024
    return plan

class User(AbstractUser):

    membership_status = models.ForeignKey(Plan, on_delete=models.PROTECT,
                                          help_text="plan the user is subscribed to",
                                          null=True,
                                          default=get_free_plan,
                                          related_name="users")
    username = models.CharField(unique=False, null=True, blank=True, max_length=30)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True,
                             validators=[RegexValidator(regex=r'^09\d{9}$',)])

    def __str__(self):
        return self.email or self.phone or self.username or "Unknown"

    def get_max_upload_size(self):
        return self.membership_status.max_upload_size

    def get_storage_quota(self):
        return self.membership_status.storage_quota

    def get_current_storage_usage(self, in_mb=False, in_gb=False):
        """
        if in_mb and in_gb are False returns the total amount of storage
        used by the user in bytes, o.w. returns it in either megabytes or gigabytes
        :param in_mb: bool
        :param in_gb: bool
        :return: int | float
        """
        total = self.files.aggregate(total=models.Sum('size'))['total']
        if in_mb:
            return total // (1024 * 1024)
        if in_gb:
            return total // (1024 ** 3)
        return total or 0

    def send_otp(self):
        if not self.phone:
            return None
        # will be replaced with a sms api code
        print(f"OTP code for {self.phone} is {self.otp_code.code}")
        return True

    def get_tokens(self) -> Dict[str, str]:
        """
        Returns a dict that contains access and refresh tokens
        """
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def validate_code(self, code: str) -> bool:
        """
        check if given code is valid for this user
        """
        if self.otp_code.code == code:
            return True
        return False

    def save(self, *args,**kwargs):
        super().save(*args, **kwargs)
        otp, _ =PhoneOTP.objects.get_or_create(user=self)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = CustomUserManager()


class PhoneOTP(BaseModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='otp_code', )
    expires_at = models.DateTimeField(null=True, default=None)
    code = models.CharField(null=True, default=None, max_length=6)

    def has_expired(self):
        """
        returns True if instance doesn't have an expires_at value,
        or simply checks if expires_at time has passed.
        """
        if not self.expires_at:
            return True
        return self.expires_at < timezone.now()

    def remaining_time(self):
        """
        returns remaining time for otp code in seconds
        """
        if not self.has_expired():
            remaining = self.expires_at - timezone.now()
            return remaining.total_seconds()
        return 0

    def generate_code(self):
        """
        generates a new code if the old one has expired, and sets
        expires_at for 5min later,
        o.w raise exception
        """
        if not self.has_expired():
            raise ValueError(f" ثانیه دوباره تلاش کنید.{self.remaining_time()}لطفا بعد از ")
        otp_code = random.randint(100000, 999999)
        otp_code = str(otp_code)[::-1]
        self.code = otp_code
        self.expires_at = timezone.now() + timedelta(minutes=5)
        self.save()
