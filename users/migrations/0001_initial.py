# Generated by Django 5.0.7 on 2024-11-11 07:29

import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import users.models.base
import users.models.verification
import users.validators
import utils.json
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True, validators=[users.validators.validate_business_email], verbose_name='Email')),
                ('email_verified', models.BooleanField(default=False, verbose_name='Email Verified')),
                ('email_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='Email Verified At')),
                ('mobile', models.CharField(blank=True, max_length=16, validators=[users.validators.validate_mobile], verbose_name='Mobile')),
                ('mobile_verified', models.BooleanField(default=False, verbose_name='Mobile Verified')),
                ('mobile_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='Mobile Verified At')),
                ('national_code', models.CharField(blank=True, max_length=16, validators=[users.validators.validate_national_code], verbose_name='National Code')),
                ('shahkar_verified', models.BooleanField(default=False, verbose_name='Shahkar Verified')),
                ('shahkar_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='Shahkar Verified At')),
                ('shahkar_response', models.TextField(blank=True, verbose_name='Shahkar Response Detail')),
                ('postal_code', models.CharField(blank=True, max_length=16, validators=[users.validators.validate_postal_code], verbose_name='Postal Code')),
                ('postal_address', models.CharField(blank=True, max_length=256, verbose_name='Postal Address')),
                ('avatar', models.ImageField(blank=True, upload_to=users.models.base.avatar_upload_to, verbose_name='Avatar')),
                ('avatar_updated_at', models.DateTimeField(editable=False, null=True, verbose_name='Avatar Updated At')),
                ('username', models.CharField(max_length=150, null=True, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='Username')),
                ('identity_verified', models.BooleanField(default=False, verbose_name='Identity Verified')),
                ('identity_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='Identity Verified At')),
                ('access_list', models.JSONField(default=list, encoder=utils.json.MessageEncoder)),
                ('roles', models.JSONField(default=list, encoder=utils.json.MessageEncoder)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('identity_verified_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='identity_verifications', to=settings.AUTH_USER_MODEL, verbose_name='Identity Verified By')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', users.models.base.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(blank=True, max_length=128, verbose_name='Name')),
                ('national_code', models.CharField(blank=True, max_length=128, verbose_name='National Code')),
                ('registry_code', models.CharField(blank=True, max_length=128, verbose_name='Registry Code')),
                ('economical_number', models.CharField(blank=True, max_length=128, verbose_name='Eco. Number')),
                ('phone', models.CharField(blank=True, max_length=128, validators=[users.validators.validate_phone], verbose_name='Phone')),
                ('postal_code', models.CharField(blank=True, max_length=128, validators=[users.validators.validate_postal_code], verbose_name='Postal Code')),
                ('postal_address', models.CharField(blank=True, max_length=128, verbose_name='Postal Address')),
                ('size', models.PositiveSmallIntegerField(null=True, verbose_name='Size')),
                ('activity_field', models.CharField(blank=True, max_length=128, verbose_name='Activity Field')),
                ('ceo_mobile', models.CharField(blank=True, max_length=16, validators=[users.validators.validate_mobile], verbose_name='CEO Mobile')),
                ('ceo_mobile_verified', models.BooleanField(default=False, verbose_name='CEO Mobile Verified')),
                ('ceo_mobile_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='CEO Mobile Verified At')),
                ('ceo_national_code', models.CharField(blank=True, max_length=16, validators=[users.validators.validate_national_code], verbose_name='CEO National Code')),
                ('ceo_shahkar_verified', models.BooleanField(default=False, verbose_name='CEO Shahkar Verified')),
                ('ceo_shahkar_verified_at', models.DateTimeField(editable=False, null=True, verbose_name='CEO Shahkar Verified At')),
                ('ceo_shahkar_response', models.TextField(blank=True, verbose_name='CEO Shahkar Response')),
                ('verified', models.BooleanField(default=False, editable=False, verbose_name='Verified')),
                ('verified_at', models.DateTimeField(editable=False, null=True, verbose_name='Verified At')),
                ('user', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='company', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to=users.models.verification.upload_doc)),
                ('tp', models.PositiveSmallIntegerField(choices=[(1, 'National ID Card'), (2, 'Founded Ad')])),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_docs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VerificationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField(editable=False)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'Sent'), (2, 'Inspecting'), (3, 'Rejected'), (4, 'Verified')], default=1, editable=False, verbose_name='Status')),
                ('inspected_at', models.DateTimeField(editable=False, null=True, verbose_name='Inspected at')),
                ('accountable_note', models.TextField(blank=True, help_text='This field is not shown to the user', verbose_name='Accountable note')),
                ('accountable_comment', models.TextField(blank=True, verbose_name='Accountable comment')),
                ('user_comment', models.TextField(blank=True, verbose_name='User comment')),
                ('accountable', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_verifications', to=settings.AUTH_USER_MODEL, verbose_name='Accountable')),
                ('content_type', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('documents', models.ManyToManyField(to='users.document', verbose_name='Documents')),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='verification_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='SentVerification',
            fields=[
            ],
            options={
                'verbose_name': 'Pending Verification Request',
                'verbose_name_plural': 'Pending Verification Requests',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.verificationrequest',),
        ),
        migrations.AddIndex(
            model_name='verificationrequest',
            index=models.Index(fields=['content_type', 'object_id'], name='users_verif_content_5cbdb0_idx'),
        ),
        migrations.AddConstraint(
            model_name='verificationrequest',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 3), _negated=True), fields=('content_type', 'object_id'), name='one_verification_request_at_a_time'),
        ),
    ]
