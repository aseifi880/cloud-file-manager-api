from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, password: str, email: str=None, phone: str=None):
        """
        Tries to create a new user if given values are valid, then creates a PhoneOTP
        instance for the created user.
        """
        try:
            email = self.normalize_email(email)
            user = self.model(email=email, phone=phone)
            user.set_password(password)
            # Custom save() creates the PhoneOTP for this user
            user.save(using=self._db)
            return user
        except Exception as e:
            raise ValueError(str(e))

    def create_superuser(self, email, password, **extra_fields):
        if not email:
            raise ValueError('کاربر باید ایمیل داشته باشد.')
        user = self.model(email=email)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)