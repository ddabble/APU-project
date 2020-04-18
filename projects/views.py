from http import HTTPStatus

import django.views.generic as django_views
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.db.models import Count, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import DeliveryForm, ProjectCategoryProposalForm, ProjectFilteringForm, ProjectForm, ProjectSortingForm, ProjectStatusForm, \
    TaskDeliveryResponseForm, TaskFileForm, TaskOfferForm, TaskOfferResponseForm, TaskPermissionForm, TeamAddForm, TeamForm
from .models import Delivery, Project, ProjectCategory, ProjectCategoryProposal, Task, TaskFile, TaskFileTeam, TaskOffer, Team, directory_path


class ProjectsView(django_views.TemplateView):
    template_name = 'projects/projects.html'
    extra_context = {
        'project_categories': ProjectCategory.objects.all(),
        'Project':            Project,
    }
    base_projects = Project.objects.prefetch_related('category', 'user_profile__user', 'tasks__offers')

    annotated_fields = {
        ProjectSortingForm.NUM_TASKS:    Count('tasks'),
        ProjectSortingForm.TOTAL_BUDGET: Sum('tasks__budget'),
        ProjectSortingForm.NUM_OFFERS:   Count('tasks__offers'),
    }

    def get(self, request, *args, **kwargs):
        context = {
            'projects':       self.base_projects,
            'sorting_form':   ProjectSortingForm(),
            'filtering_form': ProjectFilteringForm(),
        }
        kwargs.update(context)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        selected_projects = self.base_projects

        sorting_form = ProjectSortingForm(request.POST)
        filtering_form = ProjectFilteringForm(request.POST)
        if sorting_form.is_valid() and filtering_form.is_valid():
            selected_projects = self.filter_projects(selected_projects, filtering_form)
            selected_projects = self.sort_projects(selected_projects, sorting_form)

        context = {
            'projects':       selected_projects,
            'sorting_form':   sorting_form,
            'filtering_form': filtering_form,
        }
        kwargs.update(context)
        return super().get(request, *args, **kwargs)  # just returns a rendered response with context

    def sort_projects(self, projects, sorting_form: ProjectSortingForm):
        sorting_field = sorting_form.cleaned_data['sorting_field']
        ascending = sorting_form.cleaned_data['ascending']
        if sorting_field:
            if sorting_field in self.annotated_fields:
                annotation_kwarg = {sorting_field: self.annotated_fields[sorting_field]}
                projects = projects.annotate(**annotation_kwarg)
            ordering = '' if ascending else '-'
            projects = projects.order_by(f'{ordering}{sorting_field}')

        return projects

    def filter_projects(self, projects, filtering_form: ProjectFilteringForm):
        max_total_budget = filtering_form.cleaned_data['max_total_budget']
        max_num_offers = filtering_form.cleaned_data['max_num_offers']
        if any(value is not None for value in filtering_form.cleaned_data.values()):
            filtering_field_values = []
            if max_total_budget is not None:
                filtering_field_values.append((ProjectSortingForm.TOTAL_BUDGET, max_total_budget))

            if max_num_offers is not None:
                filtering_field_values.append((ProjectSortingForm.NUM_OFFERS, max_num_offers))

            for field_to_annotate, value in filtering_field_values:
                annotation_kwarg = {field_to_annotate: self.annotated_fields[field_to_annotate]}
                filter_expr = f'{field_to_annotate}__lte'
                filter_kwarg = {filter_expr: value}

                projects = projects.annotate(**annotation_kwarg).filter(**filter_kwarg)

        return projects


class ProjectCreateView(django_views.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/new_project.html'

    extra_context = {'category_proposal_form': ProjectCategoryProposalForm()}

    def get_success_url(self):
        return reverse('project_view', kwargs={'project_id': self.object.pk})

    def form_valid(self, form):
        project = form.save(commit=False)
        project.user_profile = self.request.user.profile
        project.category = get_object_or_404(ProjectCategory, pk=self.request.POST.get('category_id'))
        project.save()

        compenent_users = User.objects.filter(profile__competence_categories=project.category)
        for user in compenent_users.exclude(pk=self.request.user.pk):  # do not send email to creator
            self.send_email(user, project)

        task_title = self.request.POST.getlist('task_title')
        task_description = self.request.POST.getlist('task_description')
        task_budget = self.request.POST.getlist('task_budget')
        for i in range(len(task_title)):
            Task.objects.create(
                title=task_title[i],
                description=task_description[i],
                budget=task_budget[i],
                project=project,
            )

        return super().form_valid(form)

    def send_email(self, user: User, project: Project):
        if not user.email:
            return

        try:
            with mail.get_connection() as connection:
                mail.EmailMessage(
                    subject=f"New Project: {project.title}",
                    body="A new project you might be interested in was created and can be viwed at "
                         f"{get_current_site(self.request).domain}/projects/{project.pk}",
                    from_email="Agreelancer",
                    to=[user.email],
                    connection=connection,
                ).send()
        except Exception as e:
            messages.error(self.request, f"Sending of email to {user.email} failed: {e}")


class ProposeCategoryView(django_views.edit.BaseCreateView):
    model = ProjectCategoryProposal
    form_class = ProjectCategoryProposalForm

    def form_valid(self, form):
        self.object = form.save()
        # Return new form
        return self.form_response(self.form_class(), HTTPStatus.OK)

    def form_invalid(self, form):
        return self.form_response(form, HTTPStatus.BAD_REQUEST)

    def form_response(self, form, status: HTTPStatus):
        return render(self.request, 'projects/propose_category_form.html', self.get_context_data(category_proposal_form=form),
                      status=status)


class CategoryProposalsView(django_views.ListView):
    model = ProjectCategoryProposal
    template_name = 'projects/category_proposals.html'

    def post(self, request, *args, **kwargs):
        accept = request.POST.get('accept')
        reject = request.POST.get('reject')
        if accept is not None or reject is not None:
            category_proposal = get_object_or_404(self.model, pk=accept or reject)
            if accept is not None:
                ProjectCategory.objects.create(name=category_proposal.name)
            category_proposal.delete()

        # Redirect to same page
        return HttpResponseRedirect(request.path_info)


def project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    tasks = project.tasks.all()

    if request.user == project.user_profile.user:

        if request.method == 'POST' and 'offer_response' in request.POST:
            instance = get_object_or_404(TaskOffer, pk=request.POST.get('taskofferid'))
            offer_response_form = TaskOfferResponseForm(request.POST, instance=instance)
            if offer_response_form.is_valid():
                offer_response = offer_response_form.save(commit=False)

                if offer_response.status == TaskOffer.ACCEPTED:
                    offer_response.task.read.add(offer_response.offerer)
                    offer_response.task.write.add(offer_response.offerer)
                    project = offer_response.task.project
                    project.participants.add(offer_response.offerer)

                offer_response.save()
        offer_response_form = TaskOfferResponseForm()

        if request.method == 'POST' and 'status_change' in request.POST:
            status_form = ProjectStatusForm(request.POST)
            if status_form.is_valid():
                project_status = status_form.save(commit=False)
                project.status = project_status.status
                project.save()
        status_form = ProjectStatusForm(initial={'status': project.status})

        return render(request, 'projects/project_view.html', {
            'project':             project,
            'tasks':               tasks,
            'status_form':         status_form,
            'offer_response_form': offer_response_form,
            'Project':             Project,
            'TaskOffer':           TaskOffer,
        })

    else:
        if request.method == 'POST' and 'offer_submit' in request.POST:
            task_offer_form = TaskOfferForm(request.POST)
            if task_offer_form.is_valid():
                task_offer = task_offer_form.save(commit=False)
                task_offer.task = get_object_or_404(Task, pk=request.POST.get('taskvalue'))
                task_offer.offerer = request.user.profile
                task_offer.save()
        task_offer_form = TaskOfferForm()

        return render(request, 'projects/project_view.html', {
            'project':         project,
            'tasks':           tasks,
            'task_offer_form': task_offer_form,
            'Project':         Project,
            'TaskOffer':       TaskOffer,
        })


def is_project_owner(user, project):
    return user == project.user_profile.user


def upload_file_to_task(request, project_id, task_id):
    project = get_object_or_404(Project, pk=project_id)
    task = get_object_or_404(Task, pk=task_id)
    user_permissions = get_user_task_permissions(request.user, task)

    if user_permissions['modify'] or user_permissions['write'] or user_permissions['upload'] or is_project_owner(request.user, project):
        if request.method == 'POST':
            task_file_form = TaskFileForm(request.POST, request.FILES)
            if task_file_form.is_valid():
                task_file = task_file_form.save(commit=False)
                task_file.task = task
                existing_file = task.files.filter(file=directory_path(task_file, task_file.file.file)).first()
                access = user_permissions['modify'] or user_permissions['owner']
                for team in request.user.profile.teams.all():
                    file_modify_access = TaskFileTeam.objects.filter(team=team, file=existing_file, modify=True).exists()
                    access = access or file_modify_access
                access = access or user_permissions['modify']
                if access:
                    if existing_file:
                        existing_file.delete()
                    task_file.save()

                    if request.user.profile != project.user_profile and request.user.profile != task.accepted_task_offer.offerer:
                        teams = request.user.profile.teams.filter(task=task)
                        for team in teams:
                            tft = TaskFileTeam()
                            tft.team = team
                            tft.file = task_file
                            tft.read = True
                            tft.save()
                else:
                    messages.warning(request, "You do not have access to modify this file")

                return redirect('task_view', project_id=project_id, task_id=task_id)

        task_file_form = TaskFileForm()
        return render(request, 'projects/upload_file_to_task.html', {
            'project':        project,
            'task':           task,
            'task_file_form': task_file_form,
        })
    return redirect('/user/login')


def get_user_task_permissions(user, task):
    if user == task.project.user_profile.user:
        return {
            'write':  True,
            'read':   True,
            'modify': True,
            'owner':  True,
            'upload': True,
        }
    if task.accepted_task_offer and task.accepted_task_offer.offerer == user.profile:
        return {
            'write':  True,
            'read':   True,
            'modify': True,
            'owner':  False,
            'upload': True,
        }
    user_permissions = {
        'write':     False,
        'read':      False,
        'modify':    False,
        'owner':     False,
        'view_task': False,
        'upload':    False,
    }
    user_permissions['read'] = user_permissions['read'] or user.profile.task_participants_read.filter(pk=task.pk).exists()

    # Team members can view their teams' tasks
    user_permissions['upload'] = user_permissions['upload'] or user.profile.teams.filter(task=task, write=True).exists()
    user_permissions['view_task'] = user_permissions['view_task'] or user.profile.teams.filter(task=task).exists()

    user_permissions['write'] = user_permissions['write'] or user.profile.task_participants_write.filter(pk=task.pk).exists()
    user_permissions['modify'] = user_permissions['modify'] or user.profile.task_participants_modify.filter(pk=task.pk).exists()

    return user_permissions


class TaskView(django_views.TemplateView):
    template_name = 'projects/task_view.html'
    extra_context = {
        'Task':     Task,
        'Delivery': Delivery,
    }

    user = None
    project = None
    task = None
    user_owns_accepted_offer = None
    user_permissions = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.user = request.user
        self.project = get_object_or_404(Project, pk=kwargs['project_id'])
        self.task = get_object_or_404(Task, pk=kwargs['task_id'])
        accepted_task_offer = self.task.accepted_task_offer
        self.user_owns_accepted_offer = accepted_task_offer and accepted_task_offer.offerer == self.user.profile
        self.user_permissions = get_user_task_permissions(request.user, self.task)

    def dispatch(self, request, *args, **kwargs):
        view_permissions = self.user_permissions.copy()
        view_permissions.pop('upload', None)
        if not any(view_permissions):
            return redirect('/user/login')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'delivery-response' in request.POST:
            self.delivery_response_form(request)

        if self.user_owns_accepted_offer:
            if 'delivery' in request.POST:
                self.delivery_form(request)
            if 'team' in request.POST:
                self.team_form(request)
            if 'team-add' in request.POST:
                self.team_add_form(request)
            if 'permissions' in request.POST:
                self.permissions_form(request)

        return super().get(request, *args, **kwargs)  # just returns a rendered response with context

    def delivery_form(self, request):
        deliver_form = DeliveryForm(request.POST, request.FILES)
        if deliver_form.is_valid():
            delivery = deliver_form.save(commit=False)
            delivery.task = self.task
            delivery.delivery_user = self.user.profile
            delivery.save()
            self.task.status = Task.PENDING_ACCEPTANCE
            self.task.save()

    def delivery_response_form(self, request):
        instance = get_object_or_404(Delivery, pk=request.POST.get('delivery-id'))
        deliver_response_form = TaskDeliveryResponseForm(request.POST, instance=instance)
        if deliver_response_form.is_valid():
            delivery = deliver_response_form.save()
            delivery.responding_time = timezone.now()
            delivery.responding_user = self.user.profile
            delivery.save()

            if delivery.status == Delivery.ACCEPTED:
                self.task.status = Task.PENDING_PAYMENT
                self.task.save()
            elif delivery.status == Delivery.DECLINED:
                self.task.status = Task.DECLINED_DELIVERY
                self.task.save()

    def team_form(self, request):
        team_form = TeamForm(request.POST)
        if team_form.is_valid():
            team = team_form.save(False)
            team.task = self.task
            team.save()

    def team_add_form(self, request):
        instance = get_object_or_404(Team, pk=request.POST.get('team-id'))
        team_add_form = TeamAddForm(request.POST, instance=instance)
        if team_add_form.is_valid():
            team = team_add_form.save(False)
            team.members.add(*team_add_form.cleaned_data['members'])
            team.save()

    def permissions_form(self, request):
        for team in self.task.teams.all():
            for file in self.task.files.all():
                tft_string = f'permission-perobj-{file.pk}-{team.pk}'
                tft_id = request.POST.get(tft_string)
                try:
                    file_team = TaskFileTeam.objects.get(pk=tft_id)
                except TaskFileTeam.DoesNotExist:
                    file_team = TaskFileTeam(file=file, team=team)

                file_team.read = request.POST.get(f'permission-read-{file.pk}-{team.pk}') or False
                file_team.write = request.POST.get(f'permission-write-{file.pk}-{team.pk}') or False
                file_team.modify = request.POST.get(f'permission-modify-{file.pk}-{team.pk}') or False
                file_team.save()
            team.write = request.POST.get(f'permission-upload-{team.pk}') or False
            team.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_files = []
        teams = self.user.profile.teams.filter(task=self.task)
        per = {}
        for file in self.task.files.prefetch_related('teams__team'):
            file_name = file.name()
            per[file_name] = {}
            for file_team in file.teams.all():
                per[file_name][file_team.team.name] = file_team
                if file_team.read:
                    team_files.append(file_team)
        context.update({
            'task':                  self.task,
            'project':               self.project,
            'user_permissions':      self.user_permissions,
            'deliveries':            self.task.deliveries.all(),
            'deliver_form':          DeliveryForm(),
            'deliver_response_form': TaskDeliveryResponseForm(),
            'team_form':             TeamForm(),
            'team_add_form':         TeamAddForm(),
            'team_files':            team_files,
            'per':                   per,
        })
        return context


def task_permissions(request, project_id, task_id):
    user = request.user
    task = get_object_or_404(Task, pk=task_id)
    project = get_object_or_404(Project, pk=project_id)
    if project_id != task.project.pk:
        raise Http404(f"No task with pk={task_id} and project__pk={project_id} was found.")

    has_edit_permission = project.user_profile == user.profile or user == task.accepted_task_offer.offerer.user
    if not has_edit_permission:
        return redirect('task_view', project_id=project_id, task_id=task_id)

    if request.method == 'POST':
        task_permission_form = TaskPermissionForm(request.POST)
        if task_permission_form.is_valid():
            task_permission_form.add_permission_to_task(task)
            return redirect('task_view', project_id=project_id, task_id=task_id)

    task_permission_form = TaskPermissionForm()
    return render(request, 'projects/task_permissions.html', {
        'project': project,
        'task':    task,
        'form':    task_permission_form,
    })


def delete_file(request, file_id):
    file = get_object_or_404(TaskFile, pk=file_id)
    file.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
