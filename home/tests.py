from django.contrib.auth.models import User
from django.test import TestCase

from home.templatetags.home_extras import get_task_statuses, get_user_task_statuses
from projects.models import Project, ProjectCategory, Task, TaskOffer


class TemplateTagTests(TestCase):

    def setUp(self):
        self.password = "123456"
        self.customer = User.objects.create_user(username="customer", password=self.password)
        self.project_manager1 = User.objects.create_user(username="project_manager1", password=self.password)
        self.project_manager2 = User.objects.create_user(username="project_manager2", password=self.password)

        category1 = ProjectCategory.objects.create(name="Testing")

        self.project1 = Project.objects.create(user_profile=self.customer.profile, title="Project 1", description="Something.", category=category1)

        self.num_tasks = 0

    def _create_project_tasks(self, num: int, status: str, accept_user: User):
        for i in range(num):
            self.num_tasks += 1
            task = Task.objects.create(project=self.project1, title=f"Task {self.num_tasks}", description="Also something.", budget=100 + i, status=status)

            TaskOffer.objects.create(task=task, title=f"Offer {self.num_tasks}", description="!!", price=100 + i, offerer=accept_user.profile,
                                     status=TaskOffer.ACCEPTED, feedback="ok" * i)

    def test_task_statuses_counting_filters(self):
        self._create_project_tasks(0, Task.AWAITING_DELIVERY, self.project_manager1)
        self._create_project_tasks(1, Task.PENDING_ACCEPTANCE, self.project_manager1)
        self._create_project_tasks(2, Task.PENDING_PAYMENT, self.project_manager1)
        self._create_project_tasks(3, Task.PAYMENT_SENT, self.project_manager1)
        self._create_project_tasks(4, Task.DECLINED_DELIVERY, self.project_manager1)

        self._create_project_tasks(5, Task.AWAITING_DELIVERY, self.project_manager2)
        self._create_project_tasks(4, Task.PENDING_ACCEPTANCE, self.project_manager2)
        self._create_project_tasks(3, Task.PENDING_PAYMENT, self.project_manager2)
        self._create_project_tasks(2, Task.PAYMENT_SENT, self.project_manager2)
        self._create_project_tasks(1, Task.DECLINED_DELIVERY, self.project_manager2)

        supposed_task_statuses_for_project_manager1 = {
            'awaiting_delivery':  0,
            'pending_acceptance': 1,
            'pending_payment':    2,
            'payment_sent':       3,
            'declined_delivery':  4,
        }
        supposed_task_statuses_for_project_manager2 = {
            'awaiting_delivery':  5,
            'pending_acceptance': 4,
            'pending_payment':    3,
            'payment_sent':       2,
            'declined_delivery':  1,
        }
        self.assertDictEqual(get_user_task_statuses(self.project1, self.project_manager1), supposed_task_statuses_for_project_manager1)
        self.assertDictEqual(get_user_task_statuses(self.project1, self.project_manager2), supposed_task_statuses_for_project_manager2)

        supposed_task_statuses_for_project = {
            'awaiting_delivery':  5,
            'pending_acceptance': 5,
            'pending_payment':    5,
            'payment_sent':       5,
            'declined_delivery':  5,
        }
        self.assertDictEqual(get_task_statuses(self.project1), supposed_task_statuses_for_project)
