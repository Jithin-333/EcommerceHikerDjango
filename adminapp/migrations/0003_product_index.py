# Generated by Django 5.0.6 on 2024-06-24 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0002_rename_products_offer_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='index',
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
    ]
