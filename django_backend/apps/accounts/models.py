from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    """
    Platform user roles for Smart Parking Availability Platform.
    Admin users are managed via Django's built-in is_staff/is_superuser flags.
    """
    CUSTOMER = 'CUSTOMER', _('Customer')
    PARKING_PROVIDER = 'PARKING_PROVIDER', _('Parking Provider')


class UserProfile(models.Model):
    """
    User Profile extending Django built-in User model with platform roles and account details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        verbose_name=_('User Role'),
        help_text=_('Designates whether the user is a parking Customer or a Parking Provider.')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name=_('Phone Number')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        ordering = ['-created_at']

    @property
    def is_customer(self):
        """Return True if user has Customer role."""
        return self.role == UserRole.CUSTOMER

    @property
    def is_parking_provider(self):
        """Return True if user has Parking Provider role."""
        return self.role == UserRole.PARKING_PROVIDER

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
