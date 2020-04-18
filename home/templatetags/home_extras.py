from typing import Collection

from django import template
from django.contrib.auth.models import User

from projects.models import Project, Task, TaskOffer

register = template.Library()


@register.filter
def check_nr_pending_offers(project: Project):
    pending_offers = 0
    tasks = project.tasks.all()
    for task in tasks:
        taskoffers = task.offers.all()
        for taskoffer in taskoffers:
            if taskoffer.status == TaskOffer.PENDING:
                pending_offers += 1
    return pending_offers


@register.filter
def check_nr_user_offers(project: Project, user: User):
    offers = {}
    pending_offers = 0
    declined_offers = 0
    accepted_offers = 0
    tasks = project.tasks.all()
    for task in tasks:
        taskoffers = task.offers.filter(offerer=user.profile)
        for taskoffer in taskoffers:
            if taskoffer.status == TaskOffer.PENDING:
                pending_offers += 1
            elif taskoffer.status == TaskOffer.ACCEPTED:
                accepted_offers += 1
            elif taskoffer.status == TaskOffer.DECLINED:
                declined_offers += 1

    offers['declined'] = declined_offers
    offers['pending'] = pending_offers
    offers['accepted'] = accepted_offers
    return offers


@register.filter
def task_status(task: Task):
    status_dict = {
        Task.AWAITING_DELIVERY:  "You are awaiting delivery",
        Task.PENDING_ACCEPTANCE: "You have deliveries waiting for acceptance",
        Task.PENDING_PAYMENT:    "You have deliveries waiting for payment",
        Task.PAYMENT_SENT:       "You have sent payment",
    }
    status_dict[Task.DECLINED_DELIVERY] = status_dict[Task.AWAITING_DELIVERY]
    return status_dict[task.status]


@register.filter
def get_task_statuses(project: Project):
    return _get_status_counts(project.tasks.all())


@register.filter
def get_user_task_statuses(project: Project, user: User):
    return _get_status_counts(project.tasks.filter(offers__offerer=user.profile, offers__status=TaskOffer.ACCEPTED))


def _get_status_counts(tasks: Collection[Task]):
    task_status_counts = {status: 0 for status, status_label in Task.STATUS_CHOICES}

    for task in tasks:
        task_status_counts[task.status] += 1

    return {
        'awaiting_delivery':  task_status_counts[Task.AWAITING_DELIVERY],
        'pending_acceptance': task_status_counts[Task.PENDING_ACCEPTANCE],
        'pending_payment':    task_status_counts[Task.PENDING_PAYMENT],
        'payment_sent':       task_status_counts[Task.PAYMENT_SENT],
        'declined_delivery':  task_status_counts[Task.DECLINED_DELIVERY],
    }


@register.filter
def all_tasks(project: Project):
    return project.tasks.all()


@register.filter
def offers(task: Task):
    task_offers = task.offers.all()
    msg = "No offers"
    if task_offers:
        x = 0
        msg = "You have "
        for t in task_offers:
            x += 1
            if t.status == TaskOffer.ACCEPTED:
                return "You have accepted an offer for this task"
        msg += f"{x} pending offers"
    return msg
