# Generated by Django 5.0.9 on 2024-11-05 05:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0008_remove_subscription_permission_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscription',
            options={'permissions': [('advanced', 'Advanced Perm'), ('pro', 'Pro Perm'), ('ai', 'AI Perm')]},
        ),
    ]
