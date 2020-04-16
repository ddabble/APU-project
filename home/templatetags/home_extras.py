from typing import Collection

from django import template
from django.contrib.auth.models import User

from projects.models import Project, Task, TaskOffer

register = template.Library()


@register.filter
def check_nr_pending_offers(project):
    pending_offers = 0
    tasks = project.tasks.all()
    for task in tasks:
        taskoffers = task.offers.all()
        for taskoffer in taskoffers:
            if taskoffer.status == TaskOffer.PENDING:
                pending_offers += 1
    return pending_offers


@register.filter
def check_nr_user_offers(project, user):
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
    task_statuses = {}

    awaiting_delivery = 0
    pending_acceptance = 0
    pending_payment = 0
    payment_sent = 0
    declined_delivery = 0

    for task in tasks:
        if task.status == Task.AWAITING_DELIVERY:
            awaiting_delivery += 1
        elif task.status == Task.PENDING_ACCEPTANCE:
            pending_acceptance += 1
        elif task.status == Task.PENDING_PAYMENT:
            pending_payment += 1
        elif task.status == Task.PAYMENT_SENT:
            payment_sent += 1
        elif task.status == Task.DECLINED_DELIVERY:
            declined_delivery += 1

    task_statuses['awaiting_delivery'] = awaiting_delivery
    task_statuses['pending_acceptance'] = pending_acceptance
    task_statuses['pending_payment'] = pending_payment
    task_statuses['payment_sent'] = payment_sent
    task_statuses['declined_delivery'] = declined_delivery

    return task_statuses


@register.filter
def all_tasks(project):
    return project.tasks.all()


@register.filter
def offers(task):
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
