from rest_framework import serializers
from core.models import Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tags model object"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the ingredients model object"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ('id',)
