# Generated by Django 4.2.2 on 2024-01-10 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='market',
            name='benefit',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='market',
            name='benefit_type',
            field=models.CharField(blank=True, null=True),
        ),
    ]
