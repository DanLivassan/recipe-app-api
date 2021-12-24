from rest_framework import serializers
from core.models import Tag, Ingredient, Recipe
from django.utils.translation import ugettext_lazy as _


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


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the ingredients model object"""
    ingredients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Ingredient.objects.all())

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'ingredients', 'tags']
        read_only_fields = ('id',)

    def validate(self, attrs):
        all_ingredients_belongs_to_user = True
        all_tags_belongs_to_user = True
        if 'ingredients' in attrs:
            all_ingredients_belongs_to_user = all(
                [ingredient.user == self.context['request'].user for ingredient in attrs['ingredients']])
        if 'tags' in attrs:
            all_tags_belongs_to_user = all(
                [tag.user == self.context['request'].user for tag in attrs['tags']])
        if not (all_ingredients_belongs_to_user and all_tags_belongs_to_user):
            msg = _("Attributes doesn't belongs to user")
            raise serializers.ValidationError(msg, code='bad_request')
        return attrs


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the detailed ingredient model objects"""
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading image to recipes"""
    class Meta:
        model = Recipe
        fields = ('id', 'image',)
        read_only_fields = ('id',)