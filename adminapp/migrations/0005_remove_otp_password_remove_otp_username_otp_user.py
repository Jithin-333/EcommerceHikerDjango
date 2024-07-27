# Generated by Django 5.0.6 on 2024-06-24 11:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0004_customuser_index'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otp',
            name='password',
        ),
        migrations.RemoveField(
            model_name='otp',
            name='username',
        ),
        migrations.AddField(
            model_name='otp',
            name='user',
            field=models.ForeignKey(default=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
