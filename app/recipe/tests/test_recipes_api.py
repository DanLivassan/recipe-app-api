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

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Desert')
        payload = {
            'title': 'Grass Pie',
            'tags': [tag2.id, tag1.id],
            'time_minutes': 60,
            'price': 2
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with tags"""
        ingredient1 = sample_ingredient(user=self.user, name='Peixe')
        ingredient2 = sample_ingredient(user=self.user, name='Alho')
        ingredient3 = sample_ingredient(user=self.user, name='Cebola')
        payload = {
            'title': 'Peixe com alho e cebola',
            'ingredients': [ingredient1.id, ingredient2.id, ingredient3.id],
            'time_minutes': 120,
            'price': 38
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ingredients = Ingredient.objects.all()
        self.assertEqual(ingredients.count(), 3)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
        self.assertIn(ingredient3, ingredients)

    def test_fail_create_recipe_with_ingredients_of_other_user(self):
        """Test fail creating recipe with other user's ingredients"""
        ingredient1 = sample_ingredient(user=sample_user(email='other_user@mail.com'), name='Peixe')
        ingredient2 = sample_ingredient(user=self.user, name='Alho')
        ingredient3 = sample_ingredient(user=self.user, name='Cebola')
        payload = {
            'title': 'Peixe com alho e cebola',
            'ingredients': [ingredient1.id, ingredient2.id, ingredient3.id],
            'time_minutes': 120,
            'price': 38
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
