from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"


class Skill(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_skill_per_user')
        ]

    def has_upcoming_sessions(self):
        return self.sessions.filter(date_time__gte=timezone.now()).exists()

    def __str__(self):
        return f"{self.name}"
