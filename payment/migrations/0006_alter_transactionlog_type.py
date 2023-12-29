# Generated by Django 4.2.2 on 2023-10-02 01:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_socialsetting_link'),
        ('payment', '0005_alter_transactionlog_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionlog',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currency', to='base.currencysetting'),
        ),
    ]
