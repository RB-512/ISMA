"""
Data migration : crée les groupes 'Secretaire' et 'CDT' s'ils n'existent pas.
Ces groupes sont utilisés pour le contrôle d'accès (RBAC) dans toute l'application.
"""
from django.db import migrations


def creer_groupes(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nom_groupe in ["Secretaire", "CDT"]:
        Group.objects.get_or_create(name=nom_groupe)


def supprimer_groupes(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Secretaire", "CDT"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(creer_groupes, reverse_code=supprimer_groupes),
    ]
