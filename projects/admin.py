from django.contrib import admin

from .models import Delivery, Project, ProjectCategory, ProjectCategoryProposal, Task, TaskFile, TaskFileTeam, Team


class TaskInline(admin.TabularInline):
    model = Task
    verbose_name_plural = 'Tasks'


class ProjectAdmin(admin.ModelAdmin):
    inlines = (TaskInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return super().get_inline_instances(request, obj)
        return []


admin.site.register(Project, ProjectAdmin)
admin.site.register(Task)
admin.site.register(TaskFile)
admin.site.register(Delivery)
admin.site.register(ProjectCategory)
admin.site.register(ProjectCategoryProposal)
admin.site.register(Team)
admin.site.register(TaskFileTeam)
