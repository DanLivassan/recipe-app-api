from django.contrib.auth import get_user_model
from django.test import TestCase


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