from django.shortcuts import redirect, render

from projects.models import Project, ProjectCategoryProposal


def home(request):
    if not request.user.is_authenticated:
        return redirect('projects')

    profile = request.user.profile
    customer_projects = profile.participating_projects.all()
    team_projects = Project.objects.filter(tasks__teams__members=profile)
    return render(request, 'index.html', {
        'user_projects':          profile.projects.all(),
        'customer_projects':      set(customer_projects) | set(team_projects),
        'given_offers_projects':  Project.objects.filter(tasks__offers__offerer=profile).distinct(),
        'num_category_proposals': ProjectCategoryProposal.objects.count(),
        'Project':                Project,
    })
