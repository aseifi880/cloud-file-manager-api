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


class User(AbstractUser):

    FREE_TIER = 'free',
    PRO_TIER = 'pro',


    MEMBERSHIP_CHOICES = [
    (FREE_TIER, 'رایگان'),
        (PRO_TIER, 'ویژه'),
    ]

    membership_status = models.CharField(choices=MEMBERSHIP_CHOICES, max_length=30, default='free')
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True,
                             validators=[RegexValidator(regex=r'^09\d{9}$',)])

    def __str__(self):
        return self.username if self.username else self.email


    def get_max_upload_size(self):
        kb = 1024
        mb = 1024 * kb
        limits = {
            'free': 10 * mb,
            'pro': 100 * mb,
        }
        return limits.get(self.membership_status, 10 * mb)


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
    REQUIRED_FIELDS = []

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
