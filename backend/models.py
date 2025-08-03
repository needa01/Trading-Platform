from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=255, null=True, blank=True) 
    username = models.CharField(max_length=255, unique=True, blank=False, null=False)
    title = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True) 
    created_at = models.DateTimeField(auto_now_add=True,blank=False,null=False)
    class Meta:
        verbose_name_plural = "User"
