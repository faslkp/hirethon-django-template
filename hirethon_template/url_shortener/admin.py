from django.contrib import admin
from .models import Organization, OrganizationMembership, OrganizationInvitation, Namespace, ShortURL, BulkUploadTask


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at"]
    search_fields = ["name"]
    list_filter = ["created_at"]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "joined_at"]
    list_filter = ["role", "joined_at"]
    search_fields = ["user__email", "organization__name"]


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "organization", "role", "status", "invited_by", "created_at", "expires_at"]
    list_filter = ["status", "role", "created_at"]
    search_fields = ["email", "organization__name", "invited_by__email"]
    readonly_fields = ["token", "accepted_at"]
    actions = ["cancel_invitations"]
    
    def cancel_invitations(self, request, queryset):
        updated = queryset.filter(
            status=OrganizationInvitation.Status.PENDING
        ).update(status=OrganizationInvitation.Status.CANCELLED)
        self.message_user(request, f"{updated} invitation(s) cancelled")
    cancel_invitations.short_description = "Cancel selected invitations"


@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "created_by", "created_at"]
    search_fields = ["name", "organization__name"]
    list_filter = ["created_at"]


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ["short_code", "namespace", "original_url", "click_count", "created_by", "created_at"]
    search_fields = ["short_code", "original_url", "namespace__name"]
    list_filter = ["created_at", "is_private", "namespace"]
    readonly_fields = ["click_count"]


@admin.register(BulkUploadTask)
class BulkUploadTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "organization", "namespace", "status", "created_by", "created_at"]
    list_filter = ["status", "created_at"]
    readonly_fields = ["total_urls", "processed_urls", "failed_urls", "error_log"]

