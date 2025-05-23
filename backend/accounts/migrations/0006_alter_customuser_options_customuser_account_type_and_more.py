# Generated by Django 5.1.4 on 2025-02-22 17:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_delete_skill'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'ordering': ['-date_joined']},
        ),
        migrations.AddField(
            model_name='customuser',
            name='account_type',
            field=models.CharField(choices=[('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], default='basic', max_length=20),
        ),
        migrations.AddField(
            model_name='customuser',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_active',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_login_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='skills',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
