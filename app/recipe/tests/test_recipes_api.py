from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


def create_user(**params):
    return get_user_model().objects.create(**params)


def sample_user(email='test', password='Sstring1'):
    return create_user(**{'email': email, 'password': password})


def sample_recipe(user, **params):
    """ Create and return a sample recipe"""
    raw_recipe = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.50
    }
    raw_recipe.update(params)
    return Recipe.objects.create(user=user, **raw_recipe)


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Ingredient name'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


class PublicRecipeApiTests(TestCase):
    """ Tests recipe api not authenticated users """
    def setUp(self) -> None:
        self.client = APIClient()

    def test_required_authentication(self):
        """ Test that authentication is required for retrieving recipes """
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """ Tests recipe api authenticated users """
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_retrieving_recipe_list(self):
        """ Test that authenticated user can retrieves recipe-list data"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipe_retrieved_to_user(self):
        """ Test that recipes belongs to authenticated user"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        other_user = sample_user(email='other_user@mail.com')
        sample_recipe(user=other_user)
        sample_recipe(user=other_user)

        recipes = Recipe.objects.all()
        all_recipes_count = len(recipes)
        recipes = Recipe.objects.all().filter(user=self.user).order_by('-id')
        res = self.client.get(RECIPE_URL)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(all_recipes_count, 5)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(serializer.data, res.data)

    def test_recipe_detail_view(self):
        """Test that recipe detail is presented properly"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

