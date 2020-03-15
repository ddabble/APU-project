from django.db import models

from projects.models import Task
from user.models import Profile


class Payment(models.Model):
    payer = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name="paying_payments",
    )
    receiver = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name="receiving_payments",
    )
    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    def __str__(self):
        return f"{self.payer.user.username} {self.receiver.user.username} {self.task.budget}"
