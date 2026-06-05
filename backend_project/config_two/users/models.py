from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError('Phone number is required')
        if extra.get('email'):
            extra['email'] = self.normalize_email(extra['email'])
            
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        
        if extra.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra)

class CustomUser(AbstractUser):
    username = None
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [
        ('admin', 'Head Admin'),
        ('branch_admin', 'Branch Admin'),
        ('teacher', 'Teacher'),
    ]

    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='teacher'
    )
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"