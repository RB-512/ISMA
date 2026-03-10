from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()

ROLE_CHOICES = [
    ("Secretaire", "Secrétaire"),
    ("CDT", "Chef de Travaux"),
]


class CreerUtilisateurForm(UserCreationForm):
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2", "role"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data["role"])
            user.groups.set([group])
            EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        return user


class ModifierUtilisateurForm(forms.ModelForm):
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOICES)
    new_password = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Laisser vide pour ne pas changer"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            current_group = self.instance.groups.first()
            if current_group:
                self.fields["role"].initial = current_group.name

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data["role"])
            user.groups.set([group])
            updated = EmailAddress.objects.filter(user=user, primary=True).update(email=user.email)
            if not updated:
                EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        return user


class ModifierRoleForm(forms.Form):
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOICES)
