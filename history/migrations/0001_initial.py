# Generated by Django 2.1.5 on 2020-11-10 10:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создан')),
                ('consumer_pk', models.PositiveIntegerField(blank=True, null=True, verbose_name='Consumer PK')),
                ('action_type', models.PositiveSmallIntegerField(choices=[(1, 'Созданный объект'), (2, 'Отредактированный объект'), (3, 'Удаленный объект'), (4, 'отмена'), (5, 'Переименованный объект'), (6, 'Перемещено в корзину'), (7, 'Восстановлен из корзины')], verbose_name='Тип действия')),
                ('ip', models.CharField(max_length=15, null=True, verbose_name='IP адрес')),
                ('show_in_timeline', models.BooleanField(default=True, verbose_name='Показать на временной шкале')),
                ('consumer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_type_set_for_action', to='contenttypes.ContentType', verbose_name='Consumer Type')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Профиль')),
            ],
            options={
                'verbose_name': 'действие',
                'verbose_name_plural': 'Действия',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Diff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveIntegerField(verbose_name='Версия')),
                ('change', models.TextField()),
                ('field', models.CharField(blank=True, choices=[('number', 'number'), ('middle_name', 'middle_name'), ('phone', 'phone'), ('username', 'username'), ('series', 'series'), ('card_holder', 'card_holder'), ('email', 'email'), ('gender', 'gender'), ('date_issue', 'date_issue'), ('birthplace', 'birthplace'), ('bank_alias', 'bank_alias'), ('expiry_date', 'expiry_date'), ('document_type', 'document_type'), ('date_expiration', 'date_expiration'), ('birthday', 'birthday'), ('bank_name', 'bank_name'), ('last_name', 'last_name'), ('card_number', 'card_number'), ('first_name', 'first_name'), ('photo', 'photo')], max_length=255, null=True, verbose_name='Поле')),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='history.Action')),
            ],
            options={
                'verbose_name': 'отличие',
                'verbose_name_plural': 'Отличия',
            },
        ),
        migrations.AddField(
            model_name='action',
            name='rollback_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rolled_back_from', to='history.Diff', verbose_name='Откадить до'),
        ),
        migrations.AlterUniqueTogether(
            name='diff',
            unique_together={('action', 'field')},
        ),
        migrations.AlterIndexTogether(
            name='diff',
            index_together={('version', 'field')},
        ),
        migrations.AlterIndexTogether(
            name='action',
            index_together={('consumer_type', 'consumer_pk')},
        ),
    ]
