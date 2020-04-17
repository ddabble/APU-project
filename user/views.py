from django.contrib import messages
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render

from .forms import SignUpProfileForm, SignUpUserForm


def index(request):
    return render(request, 'base.html')


def signup(request):
    if request.method == 'POST':
        user_form = SignUpUserForm(request.POST)
        profile_form = SignUpProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False
            user.save()

            profile = profile_form.save(commit=False)
            profile.pk = user.profile.pk
            profile.user = user
            profile.save()

            raw_password = user_form.cleaned_data.get('password1')
            # No need to check for success, as the same credentials were used to create the user above
            authenticate(username=user.username, password=raw_password)
            messages.success(request, 'Your account has been created and is awaiting verification.')
            return redirect('home')
    else:
        user_form = SignUpUserForm()
        profile_form = SignUpProfileForm()
    return render(request, 'user/signup.html', {
        'user_form':    user_form,
        'profile_form': profile_form,
    })
