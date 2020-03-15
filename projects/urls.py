from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path('', views.projects, name='projects'),
    path('new/', login_required(views.new_project), name='new_project'),
    path('categories/new/', login_required(views.ProposeCategoryView.as_view()), name='propose_category'),
    path('<project_id>/', views.project_view, name='project_view'),
    path('<project_id>/tasks/<task_id>/', login_required(views.task_view), name='task_view'),
    path('<project_id>/tasks/<task_id>/upload/', login_required(views.upload_file_to_task), name='upload_file_to_task'),
    path('<project_id>/tasks/<task_id>/permissions/', login_required(views.task_permissions), name='task_permissions'),
    path('delete_file/<file_id>', login_required(views.delete_file), name='delete_file'),
]
