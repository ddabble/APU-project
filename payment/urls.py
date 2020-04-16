from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path('<int:project_id>/<int:task_id>', login_required(views.payment), name='payment'),
    path('<int:project_id>/<int:task_id>/receipt/', login_required(views.receipt), name='receipt'),
]
