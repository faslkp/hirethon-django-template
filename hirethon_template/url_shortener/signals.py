from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Organization, OrganizationMembership


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_organization(sender, instance, created, **kwargs):
    """
    Create a default organization when a new user is created.
    The user will be an admin of this organization.
    """
    if created:
        # Create organization with user's name or email
        org_name = f"{instance.name}'s Organization" if instance.name else f"{instance.email.split('@')[0]}'s Organization"
        
        organization = Organization.objects.create(
            name=org_name,
            created_by=instance
        )
        
        # Create membership with ADMIN role
        OrganizationMembership.objects.create(
            organization=organization,
            user=instance,
            role=OrganizationMembership.Role.ADMIN,
            invited_by=instance
        )

