# Generated by Django 2.2.10 on 2020-03-24 09:41

from django.db import migrations
import localflavor.generic.models


class Migration(migrations.Migration):

    dependencies = [
        ('expenseapp', '0007_auto_20200320_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='iban',
            field=localflavor.generic.models.IBANField(blank=True, include_countries=None, max_length=34, null=True, use_nordea_extensions=False, verbose_name='Bank account no'),
        ),
    ]
