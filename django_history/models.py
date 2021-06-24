from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import defaults, utils

User = get_user_model()


class Action(models.Model):
    consumer_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Consumer Type"),
        related_name="content_type_set_for_%(class)s",
        blank=True, null=True, on_delete=models.SET_NULL,
    )
    consumer_pk = models.PositiveIntegerField(_("Consumer PK"), blank=True, null=True)
    consumer = GenericForeignKey(
        ct_field="consumer_type", fk_field="consumer_pk", )
    action_type = models.PositiveSmallIntegerField(
        _('Тип действия'), choices=defaults.ACTION_TYPES)
    profile = models.ForeignKey(
        User, null=True, verbose_name=_('Профиль'), on_delete=models.SET_NULL
    )
    rollback_to = models.ForeignKey(
        'Diff', null=True, related_name='rolled_back_from',
        verbose_name=_('Откатить до'), on_delete=models.SET_NULL
    )
    ip = models.CharField(_('IP адрес'), max_length=255, null=True)
    show_in_timeline = models.BooleanField(
        _('Показать на временной шкале'), default=True)
    created_at = models.DateTimeField(_('создан'), default=timezone.now)

    def is_rollback(self):
        return self.action_type == defaults.ACTION_ROLLBACK

    def consumer_model_verbose(self):
        return self.consumer_type.model_class()._meta.verbose_name

    def __str__(self):
        return f'{self.get_action_type_display()} {self.consumer}'

    class Meta:
        verbose_name = _("действие")
        verbose_name_plural = _("Действия")
        ordering = ['-created_at']
        index_together = ('consumer_type', 'consumer_pk')


class Diff(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(_("Версия"))
    change = models.TextField()
    field = models.CharField(
        max_length=255,
        verbose_name=_("Поле"),
        null=True, blank=True
    )

    def first_version(self):
        try:
            return Diff.objects.select_related('action').order_by(
                'version').get(
                action__consumer_type__id=self.action.consumer_type_id,
                action__consumer_pk=self.action.consumer_pk,
                field=self.field, version=1)
        except Diff.DoesNotExist:
            pass

    def prev_version(self):
        try:
            return Diff.objects.select_related('action').get(
                action__consumer_type__id=self.action.consumer_type_id,
                action__consumer_pk=self.action.consumer_pk,
                field=self.field, version=self.version - 1)
        except Diff.DoesNotExist:
            pass

    def next_version(self):
        try:
            return Diff.objects.select_related('action').get(
                action__consumer_type__id=self.action.consumer_type_id,
                action__consumer_pk=self.action.consumer_pk,
                field=self.field, version=self.version + 1)
        except Diff.DoesNotExist:
            pass

    def last_version(self):
        try:
            return Diff.objects.select_related('action').filter(
                action__consumer_type__id=self.action.consumer_type_id,
                action__consumer_pk=self.action.consumer_pk,
                field=self.field).order_by('-version')[0]
        except IndexError:
            pass

    def get_version_text(self):
        return utils.merge([
            value[0] for value in self.__class__.objects.filter(
                action__consumer_type__id=self.action.consumer_type_id,
                action__consumer_pk=self.action.consumer_pk, field=self.field,
                version__lte=self.version
            ).order_by('version').values_list('change', 'version')])

    def verbose_field_name(self):
        if self.field:
            model = self.action.consumer_type.model_class()
            name = getattr(
                getattr(
                    getattr(model, self.field, None), 'fget', None),
                'verbose_name', None)
            return (name or model._meta.get_field(
                self.field)).verbose_name

    def __str__(self):
        return f'{self.verbose_field_name()}@{self.get_version_text()}'

    class Meta:
        verbose_name = _("отличие")
        verbose_name_plural = _("Отличия")
        unique_together = (
            ('action', 'field'),
        )
        index_together = ('version', 'field')
