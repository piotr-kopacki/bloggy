from django.test import TestCase
from .models import Entry, User

from django.conf import settings

import bleach
import markdown

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


class EntryTestCase(TestCase):
    def setUp(self):
        Entry.objects.create(
            pk=1,
            user=User.objects.create(
                username="TestUser", email="test@test.test", password="Test1234"
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
