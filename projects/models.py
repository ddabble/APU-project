import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Count

from user.models import Profile


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super().save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it were a true file system
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


class ProjectCategory(models.Model):
    class Meta:
        verbose_name_plural = "project categories"

    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class ProjectCategoryProposal(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'user_profile'], name="unique_title_per_user"
            ),
        ]

    user_profile = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    participants = models.ManyToManyField(
        to=Profile,
        related_name='participating_projects',
    )
    category = models.ForeignKey(
        to=ProjectCategory,
        on_delete=models.CASCADE,
        related_name='projects',
    )

    OPEN = 'o'
    INPROG = 'i'
    FINISHED = 'f'
    STATUS_CHOICES = (
        (OPEN, 'Open'),
        (INPROG, 'In progress'),
        (FINISHED, 'Finished'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=OPEN)

    @property
    def num_tasks(self):
        return len(self.tasks.all())

    @property
    def total_budget(self):
        return sum(task.budget for task in self.tasks.all())

    @property
    def num_offers(self):
        aggregation_dict = self.tasks.aggregate(num_offers=Count('offers'))
        return aggregation_dict['num_offers']

    def __str__(self):
        return self.title


class Task(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'project'], name="unique_title_per_project"
            ),
        ]

    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    budget = models.IntegerField(default=0)

    AWAITING_DELIVERY = 'ad'
    PENDING_ACCEPTANCE = 'pa'
    PENDING_PAYMENT = 'pp'
    PAYMENT_SENT = 'ps'
    DECLINED_DELIVERY = 'dd'
    STATUS_CHOICES = (
        (AWAITING_DELIVERY, 'Waiting for delivery'),
        (PENDING_ACCEPTANCE, 'Delivered and waiting for acceptance'),
        (PENDING_PAYMENT, 'Delivery has been accepted, awaiting payment'),
        (PAYMENT_SENT, 'Payment for delivery is done'),
        (DECLINED_DELIVERY, 'Declined delivery, please revise'),
    )

    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=AWAITING_DELIVERY)
    feedback = models.TextField(max_length=500, default="")

    read = models.ManyToManyField(
        to=Profile,
        related_name='task_participants_read',
    )
    write = models.ManyToManyField(
        to=Profile,
        related_name='task_participants_write',
    )
    modify = models.ManyToManyField(
        to=Profile,
        related_name='task_participants_modify',
    )

    def __str__(self):
        return f"{self.pk} {self.title}"

    @property
    def accepted_task_offer(self):
        task_offer = None
        try:
            task_offer = self.offers.get(status=TaskOffer.ACCEPTED)
        except TaskOffer.DoesNotExist:
            pass
        return task_offer


class Team(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'task'], name="unique_name_per_task"
            ),
        ]

    name = models.CharField(max_length=200)
    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    members = models.ManyToManyField(
        to=Profile,
        related_name='teams',
    )
    write = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task.project.title} - {self.task.title} - {self.name}"


def directory_path(instance, filename):
    return f'static/uploads/tasks/{instance.task.pk}/{filename}'


class TaskFile(models.Model):
    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name='files',
    )
    file = models.FileField(upload_to=directory_path, storage=OverwriteStorage())

    def name(self):
        parts = self.file.path.split("/")
        file_name = parts[-1]
        return file_name


class TaskFileTeam(models.Model):
    file = models.ForeignKey(
        to=TaskFile,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    team = models.ForeignKey(
        to=Team,
        on_delete=models.CASCADE,
        related_name='task_file_teams',
    )
    name = models.CharField(max_length=200)
    read = models.BooleanField(default=False)
    write = models.BooleanField(default=False)
    modify = models.BooleanField(default=False)


class Delivery(models.Model):
    class Meta:
        verbose_name_plural = "deliveries"

    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name='deliveries',
    )
    file = models.FileField(upload_to=directory_path)
    comment = models.TextField(max_length=500)
    delivery_user = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name='deliveries',
    )
    delivery_time = models.DateTimeField(auto_now=True)
    responding_user = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='responded_deliveries',
    )
    responding_time = models.DateTimeField(null=True, blank=True)

    ACCEPTED = 'a'
    PENDING = 'p'
    DECLINED = 'd'
    STATUS_CHOICES = (
        (ACCEPTED, 'Accepted'),
        (PENDING, 'Pending'),
        (DECLINED, 'Declined'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    feedback = models.TextField(max_length=500)


class TaskOffer(models.Model):
    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name='offers',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    price = models.IntegerField(default=0)
    offerer = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name='task_offers',
    )

    ACCEPTED = 'a'
    PENDING = 'p'
    DECLINED = 'd'
    STATUS_CHOICES = (
        (ACCEPTED, 'Accepted'),
        (PENDING, 'Pending'),
        (DECLINED, 'Declined'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    feedback = models.TextField(max_length=500)

    def calculate_average_task_offer(self):
        pass
