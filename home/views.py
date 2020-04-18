from django.shortcuts import redirect, render

from projects.models import Project, ProjectCategoryProposal


def home(request):
    if request.user.is_authenticated:
        user = request.user
        user_projects = Project.objects.filter(user_profile=user.profile)
        customer_projects = list(Project.objects.filter(participants__id=user.id))
        for team in user.profile.teams.select_related('task__project'):
            customer_projects.append(team.task.project)
        cd = {}
        for customer_project in customer_projects:
            cd[customer_project.id] = customer_project

        customer_projects = cd.values()
        given_offers_projects = get_given_offer_projects(user)
        return render(request, 'index.html', {
            'user_projects':          user_projects,
            'customer_projects':      customer_projects,
            'given_offers_projects':  given_offers_projects,
            'num_category_proposals': ProjectCategoryProposal.objects.count(),
            'Project':                Project,
        })
    else:
        return redirect('projects')


def get_given_offer_projects(user):
    projects = set()

    for taskoffer in user.profile.task_offers.select_related('task__project'):
        projects.add(taskoffer.task.project)

    return projects
