from django import forms
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm, UserCreationForm as BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError("A user with this email already exists!")
        return data

    class Meta:
        model = User
        fields = ("username", "email")


class ChangePasswordForm(BasePasswordChangeForm):
    class Meta:
        model = User
