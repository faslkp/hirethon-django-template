from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMembership, Namespace, ShortURL, BulkUploadTask

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ["id", "email", "name"]
        read_only_fields = ["id", "email", "name"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for organization membership"""
    user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "role", "invited_by", "joined_at"]
        read_only_fields = ["id", "user", "invited_by", "joined_at"]


class SimpleNamespaceSerializer(serializers.ModelSerializer):
    """Simple serializer for Namespace (without organization to avoid circular ref)"""
    url_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Namespace
        fields = ["id", "name", "created_at", "url_count"]
        read_only_fields = ["id", "created_at"]
    
    def get_url_count(self, obj):
        return obj.short_urls.count()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""
    created_by = UserSerializer(read_only=True)
    memberships = OrganizationMembershipSerializer(many=True, read_only=True)
    namespaces = SimpleNamespaceSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    namespace_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            "id", "name", "created_by", "created_at", "updated_at",
            "memberships", "namespaces", "member_count", "namespace_count", "user_role"
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
    
    def get_member_count(self, obj):
        return obj.memberships.count()
    
    def get_namespace_count(self, obj):
        return obj.namespaces.count()
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            membership = obj.memberships.filter(user=request.user).first()
            if membership:
                return membership.role
        return None


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting members to organization"""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices)
    
    def validate_email(self, value):
        # Normalize email to lowercase
        return value.lower().strip()
    
    def validate(self, data):
        from ..models import OrganizationInvitation
        organization = self.context.get('organization')
        email = data['email']
        
        # Check if user already exists and is a member
        user = User.objects.filter(email=email).first()
        if user:
            if OrganizationMembership.objects.filter(
                organization=organization,
                user=user
            ).exists():
                raise serializers.ValidationError(
                    {"email": "User is already a member of this organization."}
                )
        
        # Check if there's already a pending invitation
        if OrganizationInvitation.objects.filter(
            organization=organization,
            email=email,
            status=OrganizationInvitation.Status.PENDING
        ).exists():
            raise serializers.ValidationError(
                {"email": "An invitation has already been sent to this email."}
            )
        
        return data


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    """Serializer for Organization Invitation model"""
    organization = OrganizationSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        from ..models import OrganizationInvitation
        model = OrganizationInvitation
        fields = [
            "id", "organization", "email", "role", "token", "status",
            "invited_by", "created_at", "expires_at", "accepted_at", "is_expired"
        ]
        read_only_fields = ["id", "token", "status", "invited_by", "created_at", "accepted_at"]
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class NamespaceSerializer(serializers.ModelSerializer):
    """Serializer for Namespace model"""
    created_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source='organization',
        write_only=True
    )
    url_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Namespace
        fields = [
            "id", "name", "organization", "organization_id",
            "created_by", "created_at", "url_count"
        ]
        read_only_fields = ["id", "created_by", "created_at"]
    
    def get_url_count(self, obj):
        return obj.short_urls.count()
    
    def validate_name(self, value):
        # Check global uniqueness
        if self.instance:
            # Update case - exclude current instance
            if Namespace.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("This namespace is already taken globally.")
        else:
            # Create case
            if Namespace.objects.filter(name=value).exists():
                raise serializers.ValidationError("This namespace is already taken globally.")
        return value


class ShortURLSerializer(serializers.ModelSerializer):
    """Serializer for ShortURL model"""
    created_by = UserSerializer(read_only=True)
    namespace_id = serializers.PrimaryKeyRelatedField(
        queryset=Namespace.objects.all(),
        source='namespace',
        write_only=True
    )
    namespace = NamespaceSerializer(read_only=True)
    full_short_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ShortURL
        fields = [
            "id", "namespace", "namespace_id", "short_code", "original_url",
            "created_by", "created_at", "updated_at", "click_count",
            "expires_at", "is_private", "qr_code", "tags", "tags_list",
            "full_short_url", "is_expired"
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "click_count", "qr_code"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make short_code not required after initialization
        if 'short_code' in self.fields:
            self.fields['short_code'].required = False
            self.fields['short_code'].allow_blank = True
            self.fields['short_code'].allow_null = True
    
    def get_full_short_url(self, obj):
        request = self.context.get('request')
        if request:
            domain = request.get_host()
            return f"{request.scheme}://{domain}/{obj.namespace.name}/{obj.short_code}/"
        return obj.get_full_short_url()
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_tags_list(self, obj):
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []
    
    def to_internal_value(self, data):
        """Override to remove empty short_code before validation"""
        # Make a mutable copy of the data
        if isinstance(data, dict):
            data = data.copy()
            # Remove short_code if it's empty or just whitespace
            if 'short_code' in data:
                short_code = data['short_code']
                if short_code is None or (isinstance(short_code, str) and not short_code.strip()):
                    data.pop('short_code')
        return super().to_internal_value(data)
    
    def validate_short_code(self, value):
        """Clean and validate short_code field"""
        # Convert None or empty string to None
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value.strip()
    
    def validate(self, data):
        namespace = data.get('namespace')
        short_code = data.get('short_code')
        
        # Remove short_code from data if it's None or empty
        if short_code is None or short_code == '':
            data.pop('short_code', None)
        else:
            # If short_code is provided, validate uniqueness
            query = ShortURL.objects.filter(namespace=namespace, short_code=short_code)
            if self.instance:
                query = query.exclude(id=self.instance.id)
            
            if query.exists():
                raise serializers.ValidationError({
                    "short_code": "This short code is already taken in this namespace."
                })
        
        return data
    
    def create(self, validated_data):
        # Auto-generate short_code if not provided
        if 'short_code' not in validated_data or not validated_data.get('short_code'):
            from ..models import generate_short_code
            namespace = validated_data.get('namespace')
            
            # Generate until we find a unique one
            max_attempts = 10
            for _ in range(max_attempts):
                short_code = generate_short_code()
                if not ShortURL.objects.filter(namespace=namespace, short_code=short_code).exists():
                    validated_data['short_code'] = short_code
                    break
            else:
                raise serializers.ValidationError({
                    "short_code": "Unable to generate unique short code. Please try again."
                })
        
        return super().create(validated_data)


class BulkUploadTaskSerializer(serializers.ModelSerializer):
    """Serializer for BulkUploadTask model"""
    created_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    namespace = NamespaceSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source='organization',
        write_only=True
    )
    namespace_id = serializers.PrimaryKeyRelatedField(
        queryset=Namespace.objects.all(),
        source='namespace',
        write_only=True
    )
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkUploadTask
        fields = [
            "id", "organization", "organization_id", "namespace", "namespace_id",
            "created_by", "status", "input_file", "output_file",
            "total_urls", "processed_urls", "failed_urls", "error_log",
            "created_at", "updated_at", "progress_percentage"
        ]
        read_only_fields = [
            "id", "created_by", "status", "output_file",
            "total_urls", "processed_urls", "failed_urls", "error_log",
            "created_at", "updated_at"
        ]
    
    def get_progress_percentage(self, obj):
        if obj.total_urls > 0:
            return round((obj.processed_urls / obj.total_urls) * 100, 2)
        return 0

