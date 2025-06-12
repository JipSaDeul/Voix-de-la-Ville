# core.models

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.managers import CustomUserManager


class User(AbstractUser):
    email = models.EmailField(unique=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.username


class Admin(User):
    department = models.CharField(max_length=100, blank=True, null=True)

    @classmethod
    def from_user(cls, user):
        return cls.objects.create(
            id=user.pk,  # Ensure 1-to-1 ID mapping
            username=user.username,
            email=user.email,
            password=user.password,  # Already hashed
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
        )

    class Meta:
        verbose_name = _("Admin")
        verbose_name_plural = _("Admins")


class ReportCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Category Name")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Report Category")
        verbose_name_plural = _("Report Categories")


class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', _("Pending")),
        ('in_progress', _("In Progress")),
        ('resolved', _("Resolved")),
        ('rejected', _("Rejected")),
    ]
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("User")
    )
    category = models.ForeignKey(
        'ReportCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Category")
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title")
    )
    description = models.TextField(
        verbose_name=_("Description")
    )
    image = models.ImageField(
        upload_to='report_images/',
        blank=True,
        null=True,
        verbose_name=_("Image")
    )
    zipcode = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Zip Code")
    )
    latitude = models.FloatField(verbose_name=_("Latitude"))
    longitude = models.FloatField(verbose_name=_("Longitude"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")


class Vote(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name=_("Report")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    class Meta:
        unique_together = ('user', 'report')
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")


class Comment(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Report")
    )
    content = models.TextField(verbose_name=_("Content"))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    def __str__(self):
        return f'Comment by {self.user.username} on {self.report.title}'

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")


class AdminComment(models.Model):
    admin = models.ForeignKey(
        'Admin',
        on_delete=models.CASCADE,
        verbose_name=_("Admin")
    )
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='admin_comments',
        verbose_name=_("Report")
    )
    content = models.TextField(verbose_name=_("Content"))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    def __str__(self):
        return f'AdminComment by {self.admin.username} on {self.report.title}'

    class Meta:
        verbose_name = _("Admin Comment")
        verbose_name_plural = _("Admin Comments")


class ReportTools(models.Model):
    class Meta:
        managed = False
        verbose_name = _("Report Search")
        verbose_name_plural = _("Report Search")
