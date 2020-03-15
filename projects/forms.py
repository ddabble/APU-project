from django import forms
from django.contrib.auth.models import User

from user.models import Profile
from .models import Delivery, Project, ProjectCategory, ProjectCategoryProposal, TaskFile, TaskOffer, Team


class ProjectSortingForm(forms.Form):
    TITLE = 'title'
    NUM_TASKS = '_num_tasks'  # have to be different from any properties of the Project model, hence the underscore
    TOTAL_BUDGET = '_total_budget'
    NUM_OFFERS = '_num_offers'
    SORTING_CHOICES = (
        (None, '---'),
        (TITLE, 'Title'),
        (NUM_TASKS, 'Number of tasks'),
        (TOTAL_BUDGET, 'Total budget'),
        (NUM_OFFERS, 'Number of offers'),
    )
    sorting_field = forms.ChoiceField(choices=SORTING_CHOICES, required=False, label='Sort by:')
    ascending = forms.BooleanField(initial=True, required=False)


class ProjectFilteringForm(forms.Form):
    max_total_budget = forms.IntegerField(required=False, min_value=0, label='Max. total budget')
    max_num_offers = forms.IntegerField(required=False, min_value=0, label='Max. number of offers')


class ProjectForm(forms.ModelForm):
    title = forms.CharField(max_length=200)
    description = forms.Textarea()
    category_id = forms.ModelChoiceField(queryset=ProjectCategory.objects.all())

    class Meta:
        model = Project
        fields = ('title', 'description', 'category_id')


class ProjectCategoryProposalForm(forms.ModelForm):
    class Meta:
        model = ProjectCategoryProposal
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data['name']
        if ProjectCategory.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('Project category with this name already exists.')
            # Enforcing a unique name within the ProjectCategoryProposal model is handled by name's `unique` argument

        # Properly case the name
        name = name.title()
        return name


class TaskFileForm(forms.ModelForm):
    file = forms.FileField()

    class Meta:
        model = TaskFile
        fields = ('file',)


class ProjectStatusForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('status',)


class TaskOfferForm(forms.ModelForm):
    title = forms.CharField(max_length=200)
    description = forms.Textarea()
    price = forms.NumberInput()

    class Meta:
        model = TaskOffer
        fields = ('title', 'description', 'price',)


class TaskOfferResponseForm(forms.ModelForm):
    feedback = forms.Textarea()

    class Meta:
        model = TaskOffer
        fields = ('status', 'feedback')


class TaskDeliveryResponseForm(forms.ModelForm):
    feedback = forms.Textarea()

    class Meta:
        model = Delivery
        fields = ('status', 'feedback')


class TaskPermissionForm(forms.Form):
    PERMISSION_CHOICES = (
        ('Read', 'Read'),
        ('Write', 'Write'),
        ('Modify', 'Modify'),
    )
    user = forms.ModelChoiceField(queryset=User.objects.all())
    permission = forms.ChoiceField(choices=PERMISSION_CHOICES)


class DeliveryForm(forms.ModelForm):
    comment = forms.Textarea()
    file = forms.FileField()

    class Meta:
        model = Delivery
        fields = ('comment', 'file')


class TeamForm(forms.ModelForm):
    name = forms.CharField(max_length=50)

    class Meta:
        model = Team
        fields = ('name',)


class TeamAddForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(queryset=Profile.objects.all(), label='Members with read')

    class Meta:
        model = Team
        fields = ('members',)
