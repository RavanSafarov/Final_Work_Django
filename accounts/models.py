from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Супер админ'
        ADMIN = 'admin', 'Админ'
        USER = 'user', 'Юзер'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_banned = models.BooleanField(default=False)

    @property
    def average_rating(self):
        ratings = [offer.average_rating for offer in self.offers.all() if offer.average_rating > 0]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    @property
    def published_offers_count(self):
        return self.offers.filter(status='published').count()

    @property
    def completed_sessions_count(self):
        return self.sent_requests.filter(status='completed').count() + \
               self.received_requests.filter(status='completed').count()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.SUPERADMIN
        super().save(*args, **kwargs)

    @property
    def is_moderator(self):
        return self.role in (self.Role.ADMIN, self.Role.SUPERADMIN)