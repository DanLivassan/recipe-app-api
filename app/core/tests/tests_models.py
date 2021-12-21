from django.contrib.auth import get_user_model
from django.test import TestCase
from core import models


def sample_user(email='test@mail.com', password='Sstring1'):
    """Creste a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email_successfull(self):
        """Test creating a new user with an email successfully"""
        email = 'teste@mail.com'
        password = 'Sstring123'
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = "DANnilO@mail.cCom"
        user = get_user_model().objects.create_user(email, 'Sstring1')
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no user raise Error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'Sstring1')

    def test_create_new_super_user(self):
        """Test creating new super user"""
        user = get_user_model().objects.create_superuser('admin@mail.com', 'Sstring1')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Barbecue')
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Alho'
        )
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Moqueca de Shrimp',
            time_minutes=60,
            price=130)

        self.assertEqual(recipe.title, str(recipe))
