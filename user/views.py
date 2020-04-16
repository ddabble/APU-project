from django.contrib import messages
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render

from .forms import SignUpForm


def index(request):
    return render(request, 'base.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()

            user.profile.company = form.cleaned_data.get('company')

            user.is_active = False
            user.profile.competence_categories.add(*form.cleaned_data['competence_categories'])
            user.save()
            raw_password = form.cleaned_data.get('password1')
            # No need to check for success, as the same credentials were used to create the user above
            authenticate(username=user.username, password=raw_password)
            messages.success(request, 'Your account has been created and is awaiting verification.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'user/signup.html', {'form': form})
