# Generated by Django 5.0.7 on 2024-11-11 13:11

import users.models.base
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_verificationrequest_object_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(null=True, upload_to=users.models.base.avatar_upload_to, verbose_name='Avatar'),
        ),
    ]