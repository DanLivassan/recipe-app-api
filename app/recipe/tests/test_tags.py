from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag
from recipe.serializers import TagSerializer


GET_TAGS_URL = reverse('recipe:tag-list')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicTagsApiTests(TestCase):
    """Test the public available tags API"""
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_is_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(GET_TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Tests Authorized user tahs API"""
    def setUp(self) -> None:
        self.user = create_user(email='test@mail.com', password='Sstring1')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='Barbecue')
        Tag.objects.create(user=self.user, name='Vegan')
        res = self.client.get(GET_TAGS_URL)
        tags = Tag.objects.all().order_by('name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_is_limited_to_user(self):
        """Test that tags returned are are for the authenticated user"""
        ou_tagname = 'Other User tag'
        other_user = create_user(email='myuser@mail.com', password='passSaos')
        tag_of_other_user = Tag.objects.create(user=other_user, name=ou_tagname)
        my_tag = Tag.objects.create(user=self.user, name='MyTag')
        res = self.client.get(GET_TAGS_URL)
        self.assertEqual(len(res.data),1)
        self.assertIn(my_tag.name, str(res.data))
        self.assertNotIn(tag_of_other_user.name, str(res.data))
