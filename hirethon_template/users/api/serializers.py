from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

from hirethon_template.users.models import User as UserType


User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    class Meta:
        model = User
        fields = ["id", "email", "name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }
        read_only_fields = ["id", "email"]


class CustomRegisterSerializer(RegisterSerializer):
    """
    Custom registration serializer that includes the 'name' field
    instead of first_name and last_name
    """
    name = serializers.CharField(required=False, max_length=255, allow_blank=True)
    
    def get_cleaned_data(self):
        """Override to include name field so adapter can access it"""
        data = super().get_cleaned_data()
        data['name'] = self.validated_data.get('name', '')
        return data
