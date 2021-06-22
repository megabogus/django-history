from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, pre_delete, m2m_changed


class HistoryConfig(AppConfig):
    name = 'django_history'
    verbose_name = _('История изменений')

    def ready(self):
        from .signals import object_post_save, object_pre_delete, object_m2m_save

        post_save.connect(object_post_save)
        m2m_changed.connect(object_m2m_save)
        pre_delete.connect(object_pre_delete)

        return super().ready()
