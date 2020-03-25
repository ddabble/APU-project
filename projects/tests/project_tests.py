from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .. import views
from ..forms import TaskOfferForm
from ..models import Project, ProjectCategory, Task, TaskOffer


class ProjectTestCase(TestCase):

    def setUp(self):
        self.password = "123456"
        self.customer = User.objects.create_user(username="customer", password=self.password)
        self.project_manager = User.objects.create_user(username="project_manager", password=self.password)

        self.customer_c = Client()
        self.project_manger_c = Client()
        self.customer_c.login(username=self.customer.username, password=self.password)
        self.project_manger_c.login(username=self.project_manager.username, password=self.password)

        category1 = ProjectCategory.objects.create(name="Testing")

        self.project1 = Project.objects.create(user_profile=self.customer.profile, title="Project 1", description="Something.", category=category1)
        self.project1_task1 = Task.objects.create(project=self.project1, title="Task 1", description="Also something.", budget=100)
        self.project1_task2 = Task.objects.create(project=self.project1, title="Task 2", description="Also something 2.", budget=200)

        self.project1_url = reverse('project_view', kwargs={'project_id': self.project1.pk})


class ProjectViewTests(ProjectTestCase):

    def test_change_status(self):
        # Customer changes status from OPEN to INPROG
        self.assertEqual(self.project1.status, Project.OPEN)
        response = self.customer_c.post(self.project1_url, {'status_change': True, 'status': Project.INPROG})
        self.assertEqual(response.status_code, 200)
        self.project1.refresh_from_db(fields=['status'])
        self.assertEqual(self.project1.status, Project.INPROG)

        # Change status back
        self.customer_c.post(self.project1_url, {'status_change': True, 'status': Project.OPEN})
        self.project1.refresh_from_db(fields=['status'])
        self.assertEqual(self.project1.status, Project.OPEN)

        # User who is not project owner tries to change status
        response = self.project_manger_c.post(self.project1_url, {'status_change': True, 'status': Project.INPROG})
        self.assertEqual(response.status_code, 200)  # status code should still be OK
        # Status should not have changed
        self.project1.refresh_from_db(fields=['status'])
        self.assertEqual(self.project1.status, Project.OPEN)

    def test_task_offers(self):
        task = self.project1_task1
        # Project manager makes an offer for a task
        self.assertEqual(task.offers.count(), 0)
        response = self.project_manger_c.post(self.project1_url, {'offer_submit': True, 'taskvalue': task.pk,
                                                                  'title':        "My offer", 'description': "Nothing", 'price': 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.offers.count(), 1)

        self._test_accept_task_offer_output_coverage(task)

    def _test_accept_task_offer_output_coverage(self, task):
        task_offer = self.project_manager.profile.task_offers.get()  # will raise exception if more than 1

        self.assertNotEqual(task_offer.status, TaskOffer.ACCEPTED)
        self.assertIsNone(task.accepted_task_offer())
        self.assertEqual(task.read.count(), 0)
        self.assertEqual(task.write.count(), 0)
        self.assertEqual(task.modify.count(), 0)
        self.assertEqual(self.project1.participants.count(), 0)

        # Customer accepts offer
        customer_feedback = "All right"
        self.customer_c.post(self.project1_url, {'offer_response': True, 'taskofferid': task.pk,
                                                 'status':         TaskOffer.ACCEPTED, 'feedback': customer_feedback})
        task_offer.refresh_from_db()

        self.assertEqual(task_offer.status, TaskOffer.ACCEPTED)
        self.assertEqual(task_offer.feedback, customer_feedback)
        self.assertEqual(task.accepted_task_offer(), task_offer)
        self.assertEqual(task.read.get(), self.project_manager.profile)  # get() will raise exception if more than 1
        self.assertEqual(task.write.get(), self.project_manager.profile)  # get() will raise exception if more than 1
        self.assertEqual(task.modify.count(), 0)
        self.assertEqual(self.project1.participants.get(), self.project_manager.profile)

    def test_task_offer_boundaries(self):
        def test_task_offer_title_length(title_length: int, valid: bool):
            title = "a" * title_length
            self.assertFalse(self.project1_task1.offers.filter(title=title).exists())
            self.project_manger_c.post(self.project1_url, {'offer_submit': True, 'taskvalue': self.project1_task1.pk,
                                                           'title':        title, 'description': "Nothing", 'price': 100})
            self.assertEqual(self.project1_task1.offers.filter(title=title).exists(), valid)

        title_max_length = TaskOfferForm.declared_fields['title'].max_length
        test_task_offer_title_length(0, False)
        test_task_offer_title_length(1, True)
        test_task_offer_title_length(title_max_length, True)
        test_task_offer_title_length(title_max_length + 1, False)


class UserTaskPermissionsTests(ProjectTestCase):

    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(username="other_user", password=self.password)

    def test_get_user_task_permissions(self):
        # Customer should have all permissions for own project
        customer_permissions = views.get_user_task_permissions(self.customer, self.project1_task1)
        self.assertTrue(all(customer_permissions.values()))

        # Project manager whose offer has been accepted for the task, should have all permissions except for 'owner'
        TaskOffer.objects.create(task=self.project1_task1, title="First!", description="!!", price=100, offerer=self.project_manager.profile,
                                 status=TaskOffer.ACCEPTED, feedback="k")
        project_manager_permissions = views.get_user_task_permissions(self.project_manager, self.project1_task1)
        self.assertFalse(project_manager_permissions.pop('owner'))
        self.assertTrue(all(project_manager_permissions))

        # User who is not part of the task in any way should have no permissions
        other_user_permissions = views.get_user_task_permissions(self.other_user, self.project1_task1)
        self.assertFalse(any(other_user_permissions.values()))
