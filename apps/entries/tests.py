import bleach
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import Notification
from .models import Entry, Tag

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


User = get_user_model()


class TagTestCase(TestCase):
    def setUp(self):
        self.u = User.objects.create(
            username="testuser", email="testuser@testuser.testuser"
        )
        self.u2 = User.objects.create(
            username="testuser2", email="testuse2r@testuser2.testuser2"
        )
        self.u3 = User.objects.create(
            username="testuser3", email="testuser3@testuser3.testuser3"
        )
        self.t = Tag.objects.create(name="testtag")
        self.t2 = Tag.objects.create(name="testtag2")
        self.t.observers.add(self.u)
        self.t.observers.add(self.u2)
        self.t2.observers.add(self.u3)

    def test_notification_creation(self):
        Entry.objects.create(
            user=self.u, content="#testtag#this shouldn't create notifications"
        )
        self.assertFalse(Notification.objects.all().exists())
        Entry.objects.create(
            user=self.u, content="#testtag this should create 1 notification"
        )
        self.assertEqual(Notification.objects.all().count(), 1)
        Entry.objects.create(
            user=self.u2, content="#testtag this #should_ create 1 notification"
        )
        self.assertEqual(Notification.objects.all().count(), 2)
        Entry.objects.create(
            user=self.u3, content="#testtag this should create 2 notifications"
        )
        self.assertEqual(Notification.objects.all().count(), 4)
        Entry.objects.all().update(content="#this #should #not #create #notifications!")
        self.assertEqual(Notification.objects.all().count(), 4)

    def test_tag_creation(self):
        Entry.objects.create(
            user=self.u, content="#testtagthree this should create 1 tag"
        )
        self.assertEqual(Tag.objects.all().count(), 3)
        Entry.objects.create(
            user=self.u, content="#testTAGthree this shouldn't create a tag"
        )
        Entry.objects.create(
            user=self.u, content="#testtag#this shouldn't create a tag"
        )
        self.assertEqual(Tag.objects.all().count(), 3)
        Entry.objects.create(
            user=self.u, content="#testtag #testtagfourth should create 1 tag"
        )
        self.assertEqual(Tag.objects.all().count(), 4)


class EntryViewSetTestCase(TestCase):
    def test_soft_deletion(self):
        u = User.objects.create(username="testuser")
        e = Entry.objects.create(pk=1, user=u, content="test")
        Entry.objects.create(pk=2, user=u, content="test2", parent=e)
        e.delete()
        self.assertIsNotNone(Entry.objects.get(pk=1))
        self.assertIsNotNone(Entry.objects.get(pk=2))
        self.assertTrue(e.deleted)

    def test_hard_deletion(self):
        u = User.objects.create(username="testuser")
        e = Entry.objects.create(pk=1, user=u, content="test")
        e2 = Entry.objects.create(pk=2, user=u, content="test2", parent=e)
        e2.delete()
        e.delete()
        self.assertRaises(Entry.DoesNotExist, Entry.objects.get, pk=1)
        self.assertRaises(Entry.DoesNotExist, Entry.objects.get, pk=2)


class UserEntryTestCase(TestCase):
    def setUp(self):
        Entry.objects.create(
            pk=1,
            user=User.objects.create(
                pk=1, username="testuser", email="test@test.test", password="Test1234"
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
        self.assertEqual(User.objects.get(pk=1).points, 1)
        e = Entry.objects.create(pk=2, user=User.objects.get(pk=1))
        self.assertEqual(User.objects.get(pk=1).points, 2)
        e.upvotes.add(User.objects.get(pk=1))
        self.assertEqual(User.objects.get(pk=1).points, 3)
        Entry.objects.filter(user=User.objects.get(pk=1)).delete()
        self.assertEqual(User.objects.get(pk=1).points, 0)
