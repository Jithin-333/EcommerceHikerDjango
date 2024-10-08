# Generated by Django 5.0.6 on 2024-07-01 14:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0016_remove_variant_optionname_delete_varianoption'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='variant_detail',
        ),
        migrations.CreateModel(
            name='VariantOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='adminapp.variant')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='variant_option',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adminapp.variantoption'),
        ),
    ]
