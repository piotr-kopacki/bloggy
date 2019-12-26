from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from entries.models import Entry
from notifications.models import Notification


User = get_user_model()


class PrivateMessageAPIViewTestCase(APITestCase):
    def setUp(self):
        User.objects.create(username="testuser1", email="test1@email.com")
        User.objects.create(username="testuser2", email="test2@email.com")

    def test_user_cant_message_himself(self):
        """Ensure that users cannot message themselves"""
        user = User.objects.get(username="testuser1")
        self.client.force_authenticate(user)
        url = reverse("privatemessages-list")
        data = {"target": user.username, "text": "Test private message"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_author_cannot_change_read_attribute(self):
        """Ensure that author of a PM cant 'read' message for target"""
        user = User.objects.get(username="testuser1")
        user2 = User.objects.get(username="testuser2")
        self.client.force_authenticate(user)
        url = reverse("privatemessages-list")
        data = {"target": user2.username, "text": "Test private message"}
        response = self.client.post(url, data, format="json")
        url = reverse("privatemessages-read", kwargs={"pk": response.data["id"]})
        self.client.post(url)
        self.client.force_authenticate(user2)
        url = reverse("privatemessages-detail", kwargs={"pk": response.data["id"]})
        response = self.client.get(url)
        self.assertEqual(response.data["read"], False)

    def test_text_cannot_be_empty(self):
        """Ensure that user can't send empty PM"""
        user = User.objects.get(username="testuser1")
        user2 = User.objects.get(username="testuser2")
        self.client.force_authenticate(user)
        url = reverse("privatemessages-list")
        data = {"target": user2.username, "text": ""}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_to_user_that_exists(self):
        """Ensure that target user must exist when sending PM"""
        user = User.objects.get(username="testuser1")
        self.client.force_authenticate(user)
        url = reverse("privatemessages-list")
        data = {"target": "userDoesntExist", "text": "Test private message"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_attribute_for_author(self):
        """Ensure that, for PM author, the 'read' attribute is always True"""
        user = User.objects.get(username="testuser1")
        user2 = User.objects.get(username="testuser2")
        self.client.force_authenticate(user)
        url = reverse("privatemessages-list")
        data = {"target": user2.username, "text": "Test private message"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.data["read"], True)


class NotificationAPIViewTestCase(APITestCase):
    def test_disallow_read_false(self):
        u = User.objects.create(username="testuser")
        e = Entry.objects.create(pk=1, content="test", user=u, deleted=True)
        Notification.objects.create(
            pk=1, type="user_replied", sender=u, object=e, target=u
        )
        self.client.force_authenticate(user=u)
        url = reverse("notifications-detail", kwargs={"pk": 1})
        data = {"read": True}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = {"read": False}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_allow_authenticated_users_only(self):
        url = reverse("notifications-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_only_users_notifications(self):
        u = User.objects.create(username="testuser")
        u2 = User.objects.create(username="testuser2", email="email")
        e = Entry.objects.create(pk=1, content="test", user=u, deleted=True)
        Notification.objects.create(type="user_replied", sender=u, object=e, target=u2)
        self.client.force_authenticate(user=u)
        url = reverse("notifications-list")
        response = self.client.get(url)
        self.assertEqual(len(response.data["results"]), 0)


class EntryAPIViewTestCase(APITestCase):
    def test_allow_get_only_when_deleted(self):
        user = User.objects.create(username="testuser")
        Entry.objects.create(pk=1, content="test", user=user, deleted=True)
        self.client.force_authenticate(user=user)
        url = reverse("entry-detail", kwargs={"pk": 1})
        data = {"content": ""}
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_entry_content(self):
        user = User.objects.create(username="testuser")
        entry = Entry.objects.create(pk=1, content="test", user=user)
        Entry.objects.create(parent=entry, content="test", user=user)
        entry.delete()
        self.client.force_authenticate(user=user)
        url = reverse("entry-detail", kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.data["content"], "<p><em>deleted</em></p>")
        self.assertEqual(response.data["content_formatted"], "<p><em>deleted</em></p>")

    def test_allow_post_when_owner_only(self):
        user = User.objects.create(username="testuser")
        owner = User.objects.create(username="Owner", email="test@test.test")
        Entry.objects.create(pk=1, content="test", user=owner)
        self.client.force_authenticate(user=user)
        url = reverse("entry-detail", kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {"content": ""}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_allow_authenticated_users_only(self):
        user = User.objects.create(username="testuser")
        Entry.objects.create(pk=1, content="test", user=user)
        url = reverse("entry-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        url = reverse("entry-detail", kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
