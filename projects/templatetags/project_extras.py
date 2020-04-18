from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) if dictionary else dictionary


@register.filter
def read(per):
    return per.read if per else 0


@register.filter
def write(per):
    return per.write if per else 0


@register.filter
def modify(per):
    return per.modify if per else 0


@register.filter
def obj_pk(obj):
    return obj.pk if obj else None


@register.simple_tag
def define(val=None):
    return val


@register.filter
def check_taskoffers(task, user):
    return list(task.offers.filter(offerer=user.profile))


@register.filter
def get_all_taskoffers(task):
    return task.offers.all()


@register.filter
def get_project_participants_string(project):
    participants = project.participants.select_related('user')
    return ', '.join(set(p.user.username for p in participants))
