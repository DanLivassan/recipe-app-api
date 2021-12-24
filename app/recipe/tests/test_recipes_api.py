from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
import tempfile
import os
from PIL import Image


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


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def search_url():
    """Return URL for search recipe"""
    return reverse('recipe:recipe-search-recipe')


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

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        payload = {
            'title': 'My new recipe title',
            'time_minutes': 25,
            'price': 25
        }

        res = self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        ingredients = [
            sample_ingredient(user=self.user),
            sample_ingredient(user=self.user)
        ]
        new_ingredients = [
            sample_ingredient(user=self.user, name='Ingredient 1'),
            sample_ingredient(user=self.user, name='Ingredient 2')
        ]
        tags = [
            sample_tag(user=self.user),
            sample_tag(user=self.user)
        ]
        new_tags = [
            sample_tag(user=self.user, name='Tag 1'),
            sample_tag(user=self.user, name='Tag 2')
        ]

        recipe = sample_recipe(user=self.user)
        for ingredient in ingredients:
            recipe.ingredients.add(ingredient)
        for tag in tags:
            recipe.tags.add(tag)

        payload = {
            'title': 'My new title',
            'price': 100,
            'time_minutes': 30,
            'ingredients': [ingredient.id for ingredient in new_ingredients],
            'tags': [tag.id for tag in new_tags]
        }
        res = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            if key == 'ingredients' or key == 'tags':
                continue
            else:
                self.assertEqual(payload[key], getattr(recipe, key))
        for ingredient in recipe.ingredients.all():
            self.assertIn(ingredient, new_ingredients)
        for tag in recipe.tags.all():
            self.assertIn(tag, new_tags)


class RecipeImageUploadTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email='test@mail.com', password='Sstring1')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test upload an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf)
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'imagem'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_ingredient(self):
        """Test searching recipe by ingredient name"""
        ingredient_name = 'First Ingredient'
        ingredient = sample_ingredient(user=self.user, name=ingredient_name)
        query_params = {
            'ingredient': ingredient_name[3:8],
        }
        recipe_raw = {
            'title': 'My recipe',
            'price': 100,
            'time_minutes': 20,
        }
        recipe_raw2 = {
            'title': 'My second recipe',
            'price': 100,
            'time_minutes': 20,
        }
        recipe1 = sample_recipe(user=self.user, **recipe_raw)
        recipe2 = sample_recipe(user=self.user, **recipe_raw2)
        sample_recipe(user=self.user, **recipe_raw)
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(search_url(), query_params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        serializer = RecipeSerializer([recipe1, recipe2], many=True)
        self.assertEqual(serializer.data, res.data)

    def test_search_by_tag(self):
        """Test searching recipe by tag name"""
        tag_name = 'First tag'
        tag = sample_tag(user=self.user, name=tag_name)
        query_params = {
            'tag': tag_name[1:5],
        }
        recipe_raw = {
            'title': 'My recipe',
            'price': 100,
            'time_minutes': 20,
        }
        recipe_raw2 = {
            'title': 'My second recipe',
            'price': 100,
            'time_minutes': 20,
        }
        recipe1 = sample_recipe(user=self.user, **recipe_raw)
        recipe2 = sample_recipe(user=self.user, **recipe_raw2)
        sample_recipe(user=self.user, **recipe_raw)
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(search_url(), query_params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        serializer = RecipeSerializer([recipe1, recipe2], many=True)
        self.assertEqual(serializer.data, res.data)
