from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField


class Profile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    company = models.TextField(max_length=50, blank=True)
    phone_number = PhoneNumberField(max_length=20, blank=True)
    country = models.TextField(max_length=50, blank=True)
    state = models.TextField(max_length=50, blank=True)
    city = models.TextField(max_length=50, blank=True)
    postal_code = models.TextField(max_length=50, blank=True)
    street_address = models.TextField(max_length=50, blank=True)
    competence_categories = models.ManyToManyField(
        to='projects.ProjectCategory',  # string to avoid circular import
        related_name='competent_profiles',
    )

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, raw, **kwargs):
    # If loading a fixture (raw) or instance is saved but not created:
    if raw or not created:
        return

    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
