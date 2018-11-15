import bleach
import markdown
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .forms import UserCreationForm
from .models import Entry, User

MARKDOWN_SAMPLE = """# hello, This is Markdown Live Preview
----
## what is Markdown?
see [Wikipedia](http://en.wikipedia.org/wiki/Markdown)
> Markdown is a lightweight markup language, originally created by John Gruber and Aaron Swartz allowing people "to write using an easy-to-read, easy-to-write plain text format, then convert it to structurally valid XHTML (or HTML)".
----
## usage
1. Write markdown text in this textarea.
2. Click 'HTML Preview' button.
----
## markdown quick reference
# headers
*emphasis*
**strong**
* list
"""


class VoteViewSetTestCase(APITestCase):
    def test_allow_post_only(self):
        user = User.objects.create(username="TestUser")
        self.client.force_authenticate(user=user)
        url = reverse("vote-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(
            url, {"pk": 1, "votetype": "upvote"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.patch(
            url, {"pk": 1, "votetype": "upvote"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_vote_assignment(self):
        """
        Test if vote is correctly assigned
        """
        user = User.objects.create(username="TestUser")
        entry = Entry.objects.create(pk=1, content="test", user=user)
        self.client.force_authenticate(user=user)
        url = reverse("vote-list")
        data = {"pk": 1, "votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.upvotes.count(), 1)
        self.assertEqual(entry.downvotes.count(), 0)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.upvotes.count(), 0)
        self.assertEqual(entry.downvotes.count(), 0)
        data = {"pk": 1, "votetype": "downvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.upvotes.count(), 0)
        self.assertEqual(entry.downvotes.count(), 1)
        data = {"pk": 1, "votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.upvotes.count(), 1)
        self.assertEqual(entry.downvotes.count(), 0)

    def test_voting_requires_authentication(self):
        user = User.objects.create(username="TestUser")
        entry = Entry.objects.create(pk=1, content="test", user=user)
        url = reverse("vote-list")
        data = {"pk": 1, "votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vote_data_validation(self):
        """
        Test if view rejects non-valid data and requires all.
        """
        user = User.objects.create(username="TestUser")
        entry = Entry.objects.create(pk=1, content="test", user=user)
        self.client.force_authenticate(user=user)
        url = reverse("vote-list")
        data = {"pk": 1, "votetype": "vote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {"pk": -1, "votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = {"votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {"pk": 0}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vote_not_existing_entry(self):
        user = User.objects.create(username="TestUser")
        self.client.force_authenticate(user=user)
        url = reverse("vote-list")
        data = {"pk": 0, "votetype": "upvote"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserEntryTestCase(TestCase):
    def setUp(self):
        Entry.objects.create(
            pk=1,
            user=User.objects.create(
                pk=1, username="TestUser", email="test@test.test", password="Test1234"
            ),
            content=MARKDOWN_SAMPLE,
        )

    def test_content_formatted(self):
        """Test if content_formatted equals content as it's part of custom save method"""
        e = Entry.objects.get(pk=1)
        e.save()
        self.assertEqual(
            e.content,
            bleach.clean(
                MARKDOWN_SAMPLE, settings.MARKDOWN_TAGS, settings.MARKDOWN_ATTRS
            ),
        )

    def test_user_points(self):
        """
        Test if user's points are properly calculated
        """
        u = User.objects.get(pk=1)
        self.assertEqual(u.points, 1)
        e = Entry.objects.create(pk=2, user=u)
        self.assertEqual(u.points, 2)
        e.upvotes.add(u)
        self.assertEqual(u.points, 3)
        Entry.objects.filter(user=u).delete()
        self.assertEqual(u.points, 0)
