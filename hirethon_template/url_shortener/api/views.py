import qrcode
import openpyxl
from io import BytesIO
from urllib.parse import urlencode

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, FileResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction, models
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login
from django.contrib import messages

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied

from hirethon_template.utils.storages import MediaRootS3Boto3Storage
from ..models import Organization, OrganizationMembership, Namespace, ShortURL, BulkUploadTask, OrganizationInvitation
from .serializers import (
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    NamespaceSerializer,
    ShortURLSerializer,
    BulkUploadTaskSerializer,
    InviteMemberSerializer,
    OrganizationInvitationSerializer
)
from .permissions import IsOrgAdmin, IsOrgEditor, IsOrgMember, CanManageNamespace, CanManageShortURL
from ..tasks import process_bulk_upload_task

User = get_user_model()


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing organizations"""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return organizations where user is a member
        # Prefetch related data to avoid N+1 queries
        return Organization.objects.filter(
            memberships__user=self.request.user
        ).prefetch_related(
            'memberships__user',
            'memberships__invited_by',
            'namespaces'
        ).select_related(
            'created_by'
        ).distinct()
    
    def perform_create(self, serializer):
        # Create organization and add creator as admin
        organization = serializer.save(created_by=self.request.user)
        OrganizationMembership.objects.create(
            organization=organization,
            user=self.request.user,
            role=OrganizationMembership.Role.ADMIN,
            invited_by=self.request.user
        )
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOrgAdmin()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrgAdmin])
    def invite(self, request, pk=None):
        """Invite a member to the organization"""
        organization = self.get_object()
        serializer = InviteMemberSerializer(
            data=request.data,
            context={'organization': organization}
        )
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        
        # Check if user already exists
        user = User.objects.filter(email=email).first()
        
        if user:
            # User exists - create membership directly
            membership = OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=role,
                invited_by=request.user
            )
            
            # Send notification email
            self._send_membership_email(organization, user, role, request.user)
            
            return Response(
                OrganizationMembershipSerializer(membership).data,
                status=status.HTTP_201_CREATED
            )
        else:
            # User doesn't exist - create invitation
            invitation = OrganizationInvitation.objects.create(
                organization=organization,
                email=email,
                role=role,
                invited_by=request.user
            )
            
            # Send invitation email
            self._send_invitation_email(organization, invitation, request.user)
            
            return Response(
                {
                    "message": "Invitation sent successfully",
                    "invitation": OrganizationInvitationSerializer(invitation).data
                },
                status=status.HTTP_201_CREATED
            )
    
    def _send_invitation_email(self, organization, invitation, inviter):
        """Send invitation email to unregistered user"""
        
        # Build invitation URL
        protocol = getattr(settings, 'SITE_PROTOCOL', 'http')
        domain = getattr(settings, 'SITE_DOMAIN', 'localhost:3000')
        invite_url = f"{protocol}://{domain}/accept-invite?token={invitation.token}"
        
        subject = f"You've been invited to join {organization.name}"
        message = f"""
Hi,

{inviter.name or inviter.email} has invited you to join {organization.name} as a {invitation.role}.

Click the link below to accept the invitation and create your account:
{invite_url}

This invitation will expire in 7 days.

Best regards,
The Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invitation.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send invitation email: {e}")
    
    def _send_membership_email(self, organization, user, role, inviter):
        """Send notification email to existing user"""
        
        subject = f"You've been added to {organization.name}"
        message = f"""
Hi {user.name or user.email},

{inviter.name or inviter.email} has added you to {organization.name} as a {role}.

You can now access the organization and its resources.

Best regards,
The Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send membership email: {e}")
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsOrgMember])
    def members(self, request, pk=None):
        """List all members of the organization"""
        organization = self.get_object()
        memberships = organization.memberships.all()
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated, IsOrgAdmin])
    def remove_member(self, request, pk=None):
        """Remove a member from the organization"""
        organization = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user_id=user_id
        )
        
        # Prevent removing the last admin
        if membership.role == OrganizationMembership.Role.ADMIN:
            admin_count = organization.memberships.filter(
                role=OrganizationMembership.Role.ADMIN
            ).count()
            if admin_count <= 1:
                return Response(
                    {"error": "Cannot remove the last admin of the organization"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsOrgAdmin])
    def invitations(self, request, pk=None):
        """List all pending invitations for the organization"""
        organization = self.get_object()
        invitations = organization.invitations.filter(
            status=OrganizationInvitation.Status.PENDING
        )
        serializer = OrganizationInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrgAdmin])
    def cancel_invitation(self, request, pk=None):
        """Cancel a pending invitation"""
        organization = self.get_object()
        invitation_id = request.data.get('invitation_id')
        
        if not invitation_id:
            return Response(
                {"error": "invitation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation = get_object_or_404(
            OrganizationInvitation,
            id=invitation_id,
            organization=organization,
            status=OrganizationInvitation.Status.PENDING
        )
        
        # Delete instead of changing status to avoid unique constraint issues
        invitation.delete()
        
        return Response(
            {"message": "Invitation cancelled successfully"},
            status=status.HTTP_200_OK
        )


# Invitation acceptance endpoints (public)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_invitation(request):
    """Get invitation details by token"""
    token = request.query_params.get('token')
    
    if not token:
        return Response(
            {"error": "Token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    invitation = get_object_or_404(OrganizationInvitation, token=token)
    
    # Check if expired
    if invitation.is_expired():
        invitation.status = OrganizationInvitation.Status.EXPIRED
        invitation.save()
        return Response(
            {"error": "This invitation has expired"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already used
    if invitation.status != OrganizationInvitation.Status.PENDING:
        return Response(
            {"error": f"This invitation has already been {invitation.status.lower()}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = OrganizationInvitationSerializer(invitation)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def accept_invitation(request):
    """Accept an invitation and join the organization"""
    
    token = request.data.get('token')
    
    if not token:
        return Response(
            {"error": "Token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    invitation = get_object_or_404(OrganizationInvitation, token=token)
    
    # Check if expired
    if invitation.is_expired():
        invitation.status = OrganizationInvitation.Status.EXPIRED
        invitation.save()
        return Response(
            {"error": "This invitation has expired"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already used
    if invitation.status != OrganizationInvitation.Status.PENDING:
        return Response(
            {"error": f"This invitation has already been {invitation.status.lower()}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user email matches invitation email
    if request.user.email.lower() != invitation.email.lower():
        return Response(
            {"error": "This invitation was sent to a different email address"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user is already a member
    if OrganizationMembership.objects.filter(
        organization=invitation.organization,
        user=request.user
    ).exists():
        return Response(
            {"error": "You are already a member of this organization"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create membership
    membership = OrganizationMembership.objects.create(
        organization=invitation.organization,
        user=request.user,
        role=invitation.role,
        invited_by=invitation.invited_by
    )
    
    # Mark invitation as accepted
    invitation.status = OrganizationInvitation.Status.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save()
    
    return Response(
        {
            "message": "Invitation accepted successfully",
            "membership": OrganizationMembershipSerializer(membership).data
        },
        status=status.HTTP_201_CREATED
    )


class NamespaceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing namespaces"""
    serializer_class = NamespaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return namespaces from organizations where user is a member
        return Namespace.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()
    
    def perform_create(self, serializer):
        # Check if user is admin of the organization
        organization = serializer.validated_data['organization']
        is_admin = OrganizationMembership.objects.filter(
            organization=organization,
            user=self.request.user,
            role=OrganizationMembership.Role.ADMIN
        ).exists()
        
        if not is_admin:
            raise PermissionDenied("Only organization admins can create namespaces.")
        
        serializer.save(created_by=self.request.user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanManageNamespace()]
        return super().get_permissions()


class ShortURLViewSet(viewsets.ModelViewSet):
    """ViewSet for managing short URLs"""
    serializer_class = ShortURLSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ShortURL.objects.filter(
            namespace__organization__memberships__user=self.request.user
        ).select_related('namespace', 'namespace__organization', 'created_by').distinct()
        
        # Filter by namespace if provided
        namespace_id = self.request.query_params.get('namespace')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        # Filter by organization if provided
        organization_id = self.request.query_params.get('organization')
        if organization_id:
            queryset = queryset.filter(namespace__organization_id=organization_id)
        
        # Filter by tags if provided
        tags = self.request.query_params.get('tags')
        if tags:
            queryset = queryset.filter(tags__icontains=tags)
        
        return queryset
    
    def perform_create(self, serializer):
        # Check if user is admin or editor
        namespace = serializer.validated_data['namespace']
        is_editor_or_admin = OrganizationMembership.objects.filter(
            organization=namespace.organization,
            user=self.request.user,
            role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
        ).exists()
        
        if not is_editor_or_admin:
            raise PermissionDenied("Only organization admins and editors can create short URLs.")
        
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Override perform_update to validate permissions"""
        # Get the namespace - either from the new data or from the existing object
        namespace = serializer.validated_data.get('namespace', self.get_object().namespace)
        organization = namespace.organization
        
        # Verify user is editor or admin
        is_editor_or_admin = OrganizationMembership.objects.filter(
            organization=organization,
            user=self.request.user,
            role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
        ).exists()
        
        if not is_editor_or_admin:
            raise PermissionDenied("Only organization admins and editors can update short URLs.")
        
        serializer.save()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanManageShortURL()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate_qr(self, request, pk=None):
        """Generate QR code for the short URL"""
        short_url = self.get_object()
        
        # Check if QR code already exists and URL hasn't changed
        if short_url.qr_code and short_url.qr_code.name:
            # Verify the existing QR code is still valid by checking if file exists
            file_exists = False
            try:
                s3_storage = MediaRootS3Boto3Storage()
                file_exists = s3_storage.exists(short_url.qr_code.name)
            except Exception as e:
                file_exists = False
            
            if file_exists:
                serializer = self.get_serializer(short_url, context={'request': request})
                return Response({
                    "message": "QR code already exists",
                    "qr_code": serializer.data.get('qr_code'),
                    "full_short_url": serializer.data.get('full_short_url')
                })
        
        # Import qrcode here to avoid import errors if not installed
        try:
            # Generate full URL
            full_url = self.get_serializer(short_url, context={'request': request}).data['full_short_url']
            
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(full_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to file
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            filename = f"qr_{short_url.namespace.name}_{short_url.short_code}.png"
            
            # Use the configured storage (S3 if enabled) with fallback to local
            
            # Create ContentFile once from the buffer
            content_file = ContentFile(buffer.read())
            content_file.seek(0)  # Reset ContentFile position
            
            try:
                # Import the S3 storage class directly
                s3_storage = MediaRootS3Boto3Storage()
                file_path = s3_storage.save(f"qr_codes/{filename}", content_file)
                short_url.qr_code = file_path
                short_url.save()
            except Exception as e:
                # Fallback to local storage if S3 fails
                content_file.seek(0)
                local_storage = FileSystemStorage()
                file_path = local_storage.save(f"qr_codes/{filename}", content_file)
                short_url.qr_code = file_path
                short_url.save()
            
            serializer = self.get_serializer(short_url, context={'request': request})
            return Response({
                "message": "QR code generated successfully",
                "qr_code": serializer.data.get('qr_code'),
                "full_short_url": serializer.data.get('full_short_url')
            })
        except ImportError:
            return Response(
                {"error": "QR code generation is not available. Install qrcode library."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class BulkUploadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bulk uploads"""
    serializer_class = BulkUploadTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'post']
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def template(self, request):
        """Download Excel template for bulk upload"""
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bulk URL Upload"
        
        # Add headers
        ws.append(['original_url', 'custom_short_code'])
        
        # Add example rows
        ws.append(['https://example.com/page1', 'page1'])
        ws.append(['https://example.com/page2', ''])
        ws.append(['https://example.com/page3', 'my-custom-code'])
        
        # Style headers (bold)
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 50
        ws.column_dimensions['B'].width = 25
        
        # Save to buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="bulk_upload_template.xlsx"'
        
        return response
    
    def get_queryset(self):
        return BulkUploadTask.objects.filter(
            organization__memberships__user=self.request.user
        ).select_related('organization', 'namespace', 'created_by').distinct()
    
    def perform_create(self, serializer):
        # Check if user is admin or editor
        namespace = serializer.validated_data['namespace']
        organization = serializer.validated_data['organization']
        
        is_editor_or_admin = OrganizationMembership.objects.filter(
            organization=organization,
            user=self.request.user,
            role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
        ).exists()
        
        if not is_editor_or_admin:
            raise PermissionDenied("Only organization admins and editors can upload bulk URLs.")
        
        # Create the task
        task = serializer.save(created_by=self.request.user)
        
        # Trigger Celery task AFTER database commit to ensure task exists
        transaction.on_commit(lambda: process_bulk_upload_task.delay(task.id))
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, pk=None):
        """Download the output file"""
        task = self.get_object()
        
        if not task.output_file:
            return Response(
                {"error": "Output file is not ready yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return FileResponse(
            task.output_file.open('rb'),
            as_attachment=True,
            filename=f"bulk_upload_result_{task.id}.xlsx"
        )


class URLRedirectView(View):
    """View to handle short URL redirects"""
    
    def get(self, request, namespace, short_code):
        # Find the short URL
        try:
            short_url = ShortURL.objects.select_related('namespace').get(
                namespace__name=namespace,
                short_code=short_code
            )
        except ShortURL.DoesNotExist:
            raise Http404("Short URL not found")
        
        # Check if expired
        if short_url.is_expired():
            raise Http404("This URL has expired")
        
        # Check if private
        if short_url.is_private:
            # Check if user is authenticated via session or JWT
            user = None
            
            # Try session authentication first
            if request.user.is_authenticated:
                user = request.user
            else:
                # Try JWT token in query params or header
                token = request.GET.get('token') or request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
                
                if token:
                    try:
                        jwt_auth = JWTAuthentication()
                        validated_token = jwt_auth.get_validated_token(token)
                        user = jwt_auth.get_user(validated_token)
                    except Exception as e:
                        print(f"DEBUG: JWT authentication failed: {e}")
                        pass  # Invalid token, will show login page
                else:
                    print("DEBUG: No JWT token provided")
            
            if not user:
                # Create return URL for after login
                current_url = request.build_absolute_uri()
                return_url = urlencode({'next': current_url})
                
                # Return HTML error page with login redirect
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Private URL - Authentication Required</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f9fafb; }}
                        .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #dc2626; margin-bottom: 20px; }}
                        p {{ color: #6b7280; margin-bottom: 30px; }}
                        .login-btn {{ background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; }}
                        .login-btn:hover {{ background-color: #2563eb; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🔒 Private URL</h1>
                        <p>This is a private URL that requires authentication to access.</p>
                        <p>Please log in to your account to view this content.</p>
                        <a href="{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/auth/login/?{return_url}" class="login-btn">Go to Login</a>
                    </div>
                </body>
                </html>
                """
                return HttpResponse(html_content, content_type='text/html', status=403)
            
            # Check if user is the creator of the URL
            if user != short_url.created_by:
                print(f"DEBUG: Access denied - User {user} is not the creator {short_url.created_by}")
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Access Denied</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f9fafb; }}
                        .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #dc2626; margin-bottom: 20px; }}
                        p {{ color: #6b7280; margin-bottom: 30px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚫 Access Denied</h1>
                        <p>This is a private URL that can only be accessed by its creator.</p>
                        <p>Only the user who created this URL can access it.</p>
                    </div>
                </body>
                </html>
                """
                return HttpResponse(html_content, content_type='text/html', status=403)
            else:
                print(f"DEBUG: Access granted - User {user} is the creator of the URL")
        
        # Increment click count
        ShortURL.objects.filter(id=short_url.id).update(
            click_count=models.F('click_count') + 1
        )
        
        # Redirect to original URL
        return redirect(short_url.original_url)


class SessionLoginView(View):
    """Custom login view for session-based authentication"""
    
    def get(self, request):
        next_url = request.GET.get('next', '/')
        csrf_token = get_token(request)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Private URL Access</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f9fafb; padding: 50px; }}
                .container {{ max-width: 400px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #1f2937; margin-bottom: 30px; text-align: center; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: 500; color: #374151; }}
                input {{ width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 16px; }}
                input:focus {{ outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }}
                .login-btn {{ width: 100%; background-color: #3b82f6; color: white; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }}
                .login-btn:hover {{ background-color: #2563eb; }}
                .login-btn:disabled {{ background-color: #9ca3af; cursor: not-allowed; }}
                .error {{ color: #dc2626; margin-top: 10px; text-align: center; }}
                .frontend-link {{ text-align: center; margin-top: 20px; }}
                .frontend-link a {{ color: #3b82f6; text-decoration: none; }}
                .frontend-link a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Login Required</h1>
                <form method="post" id="loginForm">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="login-btn" id="loginBtn">Login</button>
                    <div id="error" class="error" style="display: none;"></div>
                </form>
                <div class="frontend-link">
                    <a href="{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/login">Use Frontend Login Instead</a>
                </div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error');
                    const loginBtn = document.getElementById('loginBtn');
                    
                    loginBtn.disabled = true;
                    loginBtn.textContent = 'Logging in...';
                    errorDiv.style.display = 'none';
                    
                    try {{
                        // Use form submission for session-based authentication
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = '/auth/login/';
                        
                        const emailField = document.createElement('input');
                        emailField.type = 'hidden';
                        emailField.name = 'email';
                        emailField.value = email;
                        
                        const passwordField = document.createElement('input');
                        passwordField.type = 'hidden';
                        passwordField.name = 'password';
                        passwordField.value = password;
                        
                        const nextField = document.createElement('input');
                        nextField.type = 'hidden';
                        nextField.name = 'next';
                        nextField.value = '{next_url}';
                        
                        const csrfField = document.createElement('input');
                        csrfField.type = 'hidden';
                        csrfField.name = 'csrfmiddlewaretoken';
                        csrfField.value = '{csrf_token}';
                        
                        form.appendChild(emailField);
                        form.appendChild(passwordField);
                        form.appendChild(nextField);
                        form.appendChild(csrfField);
                        document.body.appendChild(form);
                        form.submit();
                    }} catch (error) {{
                        errorDiv.textContent = 'Login failed. Please try again.';
                        errorDiv.style.display = 'block';
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Login';
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return HttpResponse(html_content, content_type='text/html')
    
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/')
        
        if email and password:
            # Authenticate user
            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Login user and create session
                login(request, user)
                # Redirect to the next URL
                return HttpResponseRedirect(next_url)
            else:
                # Authentication failed
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
        
        # If authentication failed, redirect back to login page
        return HttpResponseRedirect(f'/auth/login/?next={next_url}')

