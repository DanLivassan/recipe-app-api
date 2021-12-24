from rest_framework import viewsets, mixins, status
from rest_framework import authentication
from rest_framework import permissions
from core.models import Tag, Ingredient, Recipe
from recipe import serializers
from rest_framework.decorators import action
from rest_framework.response import Response


class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin):
    """Base ViewSet for recipe attributes (eg.: Tag, Ingredient)"""
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Returns objects for the current authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """Create a new object"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredient in the database"""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """ Manage recipe in the database """
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer

    def get_queryset(self):
        """Returns objects for the current authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        elif self.action == 'search_recipe':
            return serializers.RecipeSerializer

        return self.serializer_class

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False, url_path='search-recipe')
    def search_recipe(self, request):
        ingredient_name = request.query_params.get('ingredient')
        tag_name = request.query_params.get('tag')
        ingredients = Ingredient.objects.all().filter(name__contains=ingredient_name) if ingredient_name else []
        tags = Tag.objects.all().filter(name__contains=tag_name) if tag_name else []
        recipes = Recipe.objects.all().filter(user=self.request.user)
        if ingredients:
            recipes = recipes.filter(ingredients__in=ingredients)
        if tags:
            recipes = recipes.filter(tags__in=tags)
        serializer = serializers.RecipeSerializer(recipes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
