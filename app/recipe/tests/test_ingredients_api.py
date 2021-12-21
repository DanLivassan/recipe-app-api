from django.contrib.auth import get_user_model
from core.models import Ingredient
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENT_URL = reverse('recipe:ingredient-list')


def create_user(**params):
    return get_user_model().objects.create(**params)


class PublicIngredientApiTests(TestCase):
    """Tests the public available ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_retrieve_ingredient_is_login_required(self):
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test the private (Authorized) ingredient api"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email='test@mail.com', password='Sstring1')
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient(self):
        """ Test that retrieve ingredient list properly"""
        Ingredient.objects.create(**{
            'name': 'Ingredient 1',
            'user': self.user
        })

        Ingredient.objects.create(**{
            'name': 'Ingredient 2',
            'user': self.user
        })

        ingredients = Ingredient.objects.all()
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), len(ingredients))

    def test_ingredients_retrieved_by_user(self):
        """ Test that retrieved ingredients belongs to authenticated user"""

        Ingredient.objects.create(**{
            'name': 'Ingredient 1',
            'user': create_user(**{'email': 'other_user@mail.com', 'password': 'Sstring1'})
        })

        Ingredient.objects.create(**{
            'name': 'Ingredient 2',
            'user': self.user
        })
        Ingredient.objects.create(**{
            'name': 'Ingredient 3',
            'user': self.user
        })

        ingredients = Ingredient.objects.all().filter(user=self.user).order_by('-name')
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), len(ingredients))

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Test Ingredient'}
        self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)
