from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from phonenumber_field.formfields import PhoneNumberField

from projects.models import ProjectCategory
from .models import Profile


class SignUpUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'email_confirmation', 'password1', 'password2')

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=150)

    email = forms.EmailField(max_length=254, help_text='Input a valid email address.')
    email_confirmation = forms.EmailField(max_length=254, help_text='Enter the same email as before, for verification.')

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email_confirmation = cleaned_data.get('email_confirmation')
        if email and email_confirmation and email != email_confirmation:
            raise forms.ValidationError("Emails do not match.")

        return cleaned_data


class SignUpProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('company', 'phone_number', 'country', 'state', 'city', 'postal_code', 'street_address', 'competence_categories')

    company = forms.CharField(max_length=30, required=False, help_text='Here you can add your company.')

    phone_number = PhoneNumberField(max_length=20)

    country = forms.CharField(max_length=50)
    state = forms.CharField(max_length=50)
    city = forms.CharField(max_length=50)
    postal_code = forms.CharField(max_length=50)
    street_address = forms.CharField(max_length=50)

    competence_categories = forms.ModelMultipleChoiceField(
        queryset=ProjectCategory.objects.all(),
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.',
    )
