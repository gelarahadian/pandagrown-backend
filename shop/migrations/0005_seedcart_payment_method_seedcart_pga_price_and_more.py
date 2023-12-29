# Generated by Django 4.2.2 on 2023-10-09 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_alter_seeduser_est_harvest_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='seedcart',
            name='payment_method',
            field=models.SmallIntegerField(choices=[(0, 'pga'), (1, 'usd')], default=0),
        ),
        migrations.AddField(
            model_name='seedcart',
            name='pga_price',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='seedcart',
            name='usd_price',
            field=models.FloatField(default=0),
        ),
    ]
