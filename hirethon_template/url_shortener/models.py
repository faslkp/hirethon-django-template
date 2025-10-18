import secrets
import string
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator


def generate_short_code(length=6):
    """Generate a random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


class Organization(models.Model):
    """Organization model to group users and namespaces"""
    name = models.CharField(_("Name"), max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_organizations",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    """Membership model for users in organizations with roles"""
    
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        EDITOR = "EDITOR", _("Editor")
        VIEWER = "VIEWER", _("Viewer")

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("Organization")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        verbose_name=_("User")
    )
    role = models.CharField(
        _("Role"),
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        verbose_name=_("Invited By")
    )
    joined_at = models.DateTimeField(_("Joined At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Organization Membership")
        verbose_name_plural = _("Organization Memberships")
        unique_together = [["organization", "user"]]
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"


class OrganizationInvitation(models.Model):
    """Invitation model for inviting users to organizations via email"""
    
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")
        EXPIRED = "EXPIRED", _("Expired")
        CANCELLED = "CANCELLED", _("Cancelled")
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("Organization")
    )
    email = models.EmailField(_("Email"))
    role = models.CharField(
        _("Role"),
        max_length=10,
        choices=OrganizationMembership.Role.choices,
        default=OrganizationMembership.Role.VIEWER
    )
    token = models.CharField(
        _("Token"),
        max_length=64,
        unique=True,
        db_index=True
    )
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_org_invitations",
        verbose_name=_("Invited By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"))
    accepted_at = models.DateTimeField(_("Accepted At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Organization Invitation")
        verbose_name_plural = _("Organization Invitations")
        unique_together = [["organization", "email", "status"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "status"]),
            models.Index(fields=["token"]),
        ]
    
    def __str__(self):
        return f"Invite to {self.organization.name} for {self.email} ({self.status})"
    
    def is_expired(self):
        """Check if invitation has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        # Generate token if not set
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        
        # Set expiry if not set (7 days from now)
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)


class Namespace(models.Model):
    """Namespace model - globally unique identifier for shortened URLs"""
    name = models.SlugField(
        _("Name"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Globally unique namespace for short URLs")
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="namespaces",
        verbose_name=_("Organization")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_namespaces",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Namespace")
        verbose_name_plural = _("Namespaces")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ShortURL(models.Model):
    """Short URL model"""
    namespace = models.ForeignKey(
        Namespace,
        on_delete=models.CASCADE,
        related_name="short_urls",
        verbose_name=_("Namespace")
    )
    short_code = models.SlugField(
        _("Short Code"),
        max_length=50,
        blank=True,
        default='',
        help_text=_("Unique code within the namespace. Leave blank to auto-generate.")
    )
    original_url = models.URLField(
        _("Original URL"),
        max_length=2048,
        validators=[URLValidator()]
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_short_urls",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    click_count = models.IntegerField(_("Click Count"), default=0)
    expires_at = models.DateTimeField(
        _("Expires At"),
        null=True,
        blank=True,
        help_text=_("URL will be invalid after this date")
    )
    is_private = models.BooleanField(
        _("Is Private"),
        default=False,
        help_text=_("Private URLs require JWT authentication to access")
    )
    qr_code = models.FileField(
        _("QR Code"),
        upload_to="qr_codes/",
        null=True,
        blank=True
    )
    tags = models.CharField(
        _("Tags"),
        max_length=255,
        blank=True,
        help_text=_("Comma-separated tags")
    )

    class Meta:
        verbose_name = _("Short URL")
        verbose_name_plural = _("Short URLs")
        unique_together = [["namespace", "short_code"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["namespace", "short_code"]),
        ]

    def __str__(self):
        return f"{self.namespace.name}/{self.short_code}"

    def save(self, *args, **kwargs):
        # Generate short code if not provided
        if not self.short_code:
            # Keep trying until we find a unique code
            while True:
                code = generate_short_code()
                if not ShortURL.objects.filter(
                    namespace=self.namespace,
                    short_code=code
                ).exists():
                    self.short_code = code
                    break
        super().save(*args, **kwargs)

    def get_full_short_url(self, domain=""):
        """Get the full shortened URL"""
        if not domain:
            from django.conf import settings
            protocol = getattr(settings, 'SITE_PROTOCOL', 'http')
            domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
            return f"{protocol}://{domain}/{self.namespace.name}/{self.short_code}/"
        return f"{domain}/{self.namespace.name}/{self.short_code}/"

    def is_expired(self):
        """Check if the URL has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class BulkUploadTask(models.Model):
    """Track bulk URL upload tasks"""
    
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PROCESSING = "PROCESSING", _("Processing")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="bulk_upload_tasks",
        verbose_name=_("Organization")
    )
    namespace = models.ForeignKey(
        Namespace,
        on_delete=models.CASCADE,
        related_name="bulk_upload_tasks",
        verbose_name=_("Namespace")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bulk_upload_tasks",
        verbose_name=_("Created By")
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    input_file = models.FileField(
        _("Input File"),
        upload_to="bulk_uploads/input/"
    )
    output_file = models.FileField(
        _("Output File"),
        upload_to="bulk_uploads/output/",
        null=True,
        blank=True
    )
    total_urls = models.IntegerField(_("Total URLs"), default=0)
    processed_urls = models.IntegerField(_("Processed URLs"), default=0)
    failed_urls = models.IntegerField(_("Failed URLs"), default=0)
    error_log = models.TextField(_("Error Log"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Bulk Upload Task")
        verbose_name_plural = _("Bulk Upload Tasks")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bulk Upload {self.id} - {self.status}"

