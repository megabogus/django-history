# Generated by Django 3.1.6 on 2021-08-15 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_history', '0002_auto_20210624_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='создан'),
        ),
    ]
