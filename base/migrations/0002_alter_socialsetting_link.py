# Generated by Django 4.2.2 on 2023-09-25 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialsetting',
            name='link',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
