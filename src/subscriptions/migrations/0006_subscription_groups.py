# Generated by Django 5.0.9 on 2024-11-05 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('subscriptions', '0005_alter_subscription_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='groups',
            field=models.ManyToManyField(to='auth.group'),
        ),
    ]
