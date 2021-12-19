from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the users objects"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'is_active', 'is_staff', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5}
        }

    def create(self, validated_data):
        """Create a new user with encrypted password and returns it"""
        return get_user_model().objects.create_user(**validated_data)
