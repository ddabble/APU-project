from django.contrib import admin

from util.utils import HtmlUtils
from .models import Delivery, Project, ProjectCategory, ProjectCategoryProposal, Task, TaskFile, TaskFileTeam, TaskOffer, Team


class ProjectAdmin(admin.ModelAdmin):
    class TaskInline(admin.TabularInline):
        model = Task
        verbose_name_plural = 'Tasks'
        extra = 0

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.prefetch_related('read__user', 'write__user', 'modify__user')

    inlines = [TaskInline]

    list_display = ('title', 'user_profile', 'get_tasks', 'get_budgets', 'get_offers', 'get_participants', 'category', 'status')
    list_filter = ('category', 'status')
    search_fields = ('title', 'description', 'tasks__title', 'user_profile__user__username', 'participants__user__username')
    ordering = ['user_profile', 'title']

    raw_id_fields = ('user_profile',)
    filter_horizontal = ('participants',)

    def get_tasks(self, project):
        return HtmlUtils.block_join(project.tasks.all(), sep=HtmlUtils.EN_DASH)

    get_tasks.short_description = 'Tasks'

    def get_budgets(self, project):
        return HtmlUtils.block_join([t.budget for t in project.tasks.all()], sep=HtmlUtils.EN_DASH)

    get_budgets.short_description = 'Budgets'

    def get_offers(self, project):
        return HtmlUtils.block_join([len(t.offers.all()) for t in project.tasks.all()], sep=HtmlUtils.EN_DASH)

    get_offers.short_description = 'Offers'

    def get_participants(self, project):
        return HtmlUtils.block_join(project.participants.all())

    get_participants.short_description = 'Participants'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('tasks__offers', 'participants')


admin.site.register(ProjectCategory)
admin.site.register(ProjectCategoryProposal)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Task)
admin.site.register(Team)
admin.site.register(TaskFile)
admin.site.register(TaskFileTeam)
admin.site.register(Delivery)
admin.site.register(TaskOffer)
