# Generated by Django 5.0.6 on 2024-06-27 08:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0010_product_offer_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='offer_price',
        ),
    ]
