from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project, Task
from .forms import PaymentForm
from .models import Payment


def payment(request, project_id, task_id):
    task = get_object_or_404(Task, pk=task_id)
    sender = get_object_or_404(Project, pk=project_id).user_profile
    receiver = task.accepted_task_offer.offerer

    if request.method == 'POST':
        payment = Payment(payer=sender, receiver=receiver, task=task)
        payment.save()
        task.status = Task.PAYMENT_SENT
        task.save()

        return redirect('receipt', project_id=project_id, task_id=task_id)

    return render(request, 'payment/payment.html', {'form': PaymentForm()})


def receipt(request, project_id, task_id):
    project = get_object_or_404(Project, pk=project_id)
    task = get_object_or_404(Task, pk=task_id)
    taskoffer = task.accepted_task_offer

    return render(request, 'payment/receipt.html', {
        'project':   project,
        'task':      task,
        'taskoffer': taskoffer,
    })
