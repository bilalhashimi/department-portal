# Generated by Django 4.2.21 on 2025-06-03 02:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('departments', '0005_add_activity_tracking_and_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentvisibility',
            name='allowed_departments',
        ),
        migrations.RemoveField(
            model_name='documentvisibility',
            name='allowed_users',
        ),
        migrations.RemoveField(
            model_name='documentvisibility',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='useractivity',
            name='user',
        ),
        migrations.DeleteModel(
            name='DocumentDeletionRequest',
        ),
        migrations.DeleteModel(
            name='DocumentVisibility',
        ),
        migrations.DeleteModel(
            name='UserActivity',
        ),
    ]
