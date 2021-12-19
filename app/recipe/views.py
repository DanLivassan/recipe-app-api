from rest_framework import viewsets, mixins
from rest_framework import authentication
from rest_framework import permissions
from core.models import Tag
from recipe import serializers


class TagViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Manage tags in the database"""
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        """Returns objects for the current authenticated user"""
        return Tag.objects.all().filter(user=self.request.user)

