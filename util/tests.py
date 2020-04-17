from django.contrib.auth.models import User
from django.test import TestCase

from util.utils import HtmlUtils


class HtmlUtilsTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

    def test_block_join(self):
        supposed_html = """
        <div style="white-space: nowrap;">
            <b>&bull;</b> user1
        </div>
        <div style="white-space: nowrap;">
            <b>&bull;</b> user2
        </div>"""
        self.assertHTMLEqual(HtmlUtils.block_join([self.user1, self.user2]), supposed_html)

        supposed_html = """
        <div style="white-space: nowrap;">
            &ndash; 123
        </div>"""
        self.assertHTMLEqual(HtmlUtils.block_join([123], sep="&ndash;"), supposed_html)
        supposed_html += """
        <div style="white-space: nowrap;">
            &ndash; 234
        </div>"""
        self.assertHTMLEqual(HtmlUtils.block_join([123, 234], sep="&ndash;"), supposed_html)

        supposed_html = """
        <div style="display: inline-block; white-space: nowrap;">
            111
        </div>"""
        self.assertHTMLEqual(HtmlUtils.block_join([111], sep="|", multiline=False), supposed_html)
        supposed_html += """
        <div style="display: inline-block; white-space: nowrap;">
            | 222
        </div>"""
        self.assertHTMLEqual(HtmlUtils.block_join([111, 222], sep="|", multiline=False), supposed_html)

        self.assertHTMLEqual(HtmlUtils.block_join([]), "")
        self.assertHTMLEqual(HtmlUtils.block_join([], multiline=False), "")

        empty_queryset = User.objects.filter(username="")
        self.assertHTMLEqual(HtmlUtils.block_join(empty_queryset), "")
        self.assertHTMLEqual(HtmlUtils.block_join(empty_queryset, multiline=False), "")
