from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()

ROLE_CHOICES = [
    ("Secrétaire", "Secrétaire"),
    ("CDT", "Chef de Travaux"),
]


class CreerUtilisateurForm(UserCreationForm):
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2", "role"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data["role"])
            user.groups.set([group])
        return user


class ModifierRoleForm(forms.Form):
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOICES)
