# Generated by Django 5.0.9 on 2024-11-08 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0012_usersubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='stripe_id',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
