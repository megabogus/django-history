import logging
import itertools
import operator
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Action, Diff
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType


logger = logging.getLogger(__name__)


def get_content_type_for_model(obj):
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


class HistoryBlockAdmin(object):

    def history_view(self, request, object_id, extra_context=None):
        model = self.model
        opts = model._meta
        action_list = Action.objects.filter(
            consumer_pk=unquote(object_id),
            consumer_type=get_content_type_for_model(model),
        ).order_by('-created_at')
        if self.inlines:
            for inline in self.inlines:
                for f in inline.model._meta.local_fields:
                    if f.remote_field and f.remote_field.model == model:
                        logger.info(f"{f.name}")
                        qs = {f"{f.name}_id": object_id}
                        ids = [obj.pk for obj in inline.model.objects.filter(**qs)]
                        action_list = itertools.chain(
                            action_list,
                            Action.objects.filter(
                                consumer_pk__in=ids,
                                consumer_type=get_content_type_for_model(inline.model),
                            ).order_by('-created_at')
                        )
            action_list = list(action_list)
        extra_context = {
            'action_list': action_list,
            'opts': opts,
            'history': Action._meta,
            **(extra_context or {}),
        }
        self.object_history_template = "history/admin/list.html"

        request.current_app = self.admin_site.name
        return super().history_view(request, object_id, extra_context=extra_context)


class DiffAdminInlines(admin.StackedInline):
    model = Diff
    exclude = ['change']
    extra = 0
    max_num = 0
    can_delete = False
    readonly_fields = ('version', 'change_html', 'field', 'field_name')

    def change_html(self, instance):
        return format_html_join(
            mark_safe('<br>'),
            '<span style="{}">{}</span>',
            (
                ('color:#cc0000;' if line.startswith('-') else
                 ('color:#008800;' if line.startswith('+') else
                  ('color:#990099;' if line.startswith('@') else '')),
                 conditional_escape(line)) for line in instance.change.splitlines()
            )
        )

    change_html.short_description = _("Изменения")

    def field_name(self, instance):
        return instance.verbose_field_name()

    field_name.short_description = _('Название поля')


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'ip', 'diffs', 'created_at')
    readonly_fields = (
        'consumer_type', 'consumer_pk', 'consumer', 'action_type', 'profile', 'rollback_to', 'ip', 'show_in_timeline',
        'created_at'
    )
    inlines = [DiffAdminInlines]

    def diffs(self, obj):
        if obj.diff_set.all():
            return format_html_join(
                mark_safe('<br>'),
                '{}',
                ((diff,) for diff in obj.diff_set.all())
            )
        else:
            return "-"

    diffs.short_description = _("Изменения")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(ActionAdmin, self).change_view(request, object_id, extra_context=extra_context)
