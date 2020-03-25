from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..models import ProjectCategory, ProjectCategoryProposal


class ProjectCategoryProposalTests(TestCase):

    def setUp(self):
        ProjectCategory.objects.create(name="Category 1")
        ProjectCategory.objects.create(name="Category 2")
        ProjectCategory.objects.create(name="Category 3")

        password = "123456"
        customer = User.objects.create_user("customer", password=password)
        admin = User.objects.create_user("admin", password=password, is_staff=True, is_superuser=True)

        self.customer_c = Client()
        self.admin_c = Client()
        self.customer_c.login(username=customer.username, password=password)
        self.admin_c.login(username=admin.username, password=password)

    def test_proposals_appear_on_proposals_page(self):
        category_1_name = "yddc44Apo8H4YP3M"
        category_2_name = "GpSkBjnk5eTjNsNy".title()

        def appears_on_proposals_page(text: str):
            _response = self.admin_c.get(reverse('category_proposals'))
            self.assertContains(_response, text)

        response = self.customer_c.post(reverse('propose_category'), {'name': category_1_name})
        self.assertEqual(response.status_code, 200)
        appears_on_proposals_page(category_1_name.title())

        response = self.customer_c.post(reverse('propose_category'), {'name': category_1_name.lower()})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST.value)

        response = self.customer_c.post(reverse('propose_category'), {'name': category_2_name})
        self.assertEqual(response.status_code, 200)
        appears_on_proposals_page(category_2_name)

        self._test_proposals_disappear_from_proposals_page(category_1_name.title(), category_2_name)

    def _test_proposals_disappear_from_proposals_page(self, category_1_name: str, category_2_name: str):
        category_1 = ProjectCategoryProposal.objects.get(name=category_1_name)
        response = self.admin_c.post(reverse('category_proposals'), {'accept': category_1.pk}, follow=True)
        self.assertNotContains(response, category_1_name)

        category_2 = ProjectCategoryProposal.objects.get(name=category_2_name)
        response = self.admin_c.post(reverse('category_proposals'), {'reject': category_2.pk}, follow=True)
        self.assertNotContains(response, category_2_name)

        self._test_new_categories_appear_on_projects_page(category_1_name, category_2_name)

    def _test_new_categories_appear_on_projects_page(self, category_1_name: str, category_2_name: str):
        response = self.customer_c.get(reverse('projects'))
        self.assertContains(response, category_1_name)
        self.assertNotContains(response, category_2_name)
