import logging
import datetime
import difflib
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.db import transaction
from . import defaults, utils
from .models import Diff, Action
from .middleware import get_current_ip, get_current_user
import threading

logger = logging.getLogger(__name__)


def get_last_version(consumer_type, consumer_pk, field):
    try:
        return Diff.objects.filter(
            action__consumer_type=consumer_type,
            action__consumer_pk=consumer_pk, field=field
        ).order_by('-version')[0].version
    except IndexError:
        return 0


class CreateDiff(threading.Thread):
    def __init__(self, sender_name, consumer_type, instance=None, created=None, profile=None, ip=None, **kwargs):
        self.sender_name = sender_name
        self.consumer_type = consumer_type
        self.instance = instance
        self.created = created
        self.profile = profile
        self.ip = ip
        super(CreateDiff, self).__init__(**kwargs)

    @transaction.atomic
    def run(self):

        instance = self.instance

        if hasattr(instance, '_action_type'):
            action_type = instance._action_type
            delattr(instance, '_action_type')
        else:
            action_type = (
                defaults.ACTION_CREATE if self.created else
                defaults.ACTION_EDIT)

        if action_type == defaults.ACTION_ROLLBACK:
            return

        timeline_observed = utils.is_observed(self.sender_name, action_type)
        if not ((self.sender_name in defaults.OBSERVED_FIELDS) or timeline_observed):
            return

        if action_type == defaults.ACTION_EDIT:
            if Action.objects.filter(
                consumer_type=self.consumer_type, consumer_pk=instance.pk,
                action_type__in=(defaults.ACTION_CREATE, defaults.ACTION_EDIT),
                created_at__gte=datetime.datetime.now()
            ).exists():
                instance._ignore_in_timeline = True
        try:
            _ignore_in_timeline = getattr(instance, '_ignore_in_timeline', False)
        except ValueError as e:
            logger.info("Ignore in timeline: {}".format(e))
            _ignore_in_timeline = False

        try:
            provider = Action.objects.create(
                consumer_type=self.consumer_type, consumer_pk=instance.pk,
                action_type=action_type, profile=self.profile, ip=self.ip,
                show_in_timeline=_ignore_in_timeline)
        except ValueError as e:
            logger.warning("Value Error: {}".format(e))
            return

        if action_type == defaults.ACTION_CREATE:
            instance._ignore_in_timeline = True

        fields = (
            set(defaults.OBSERVED_FIELDS.get(self.sender_name, ()))
        )
        if fields:
            consumer_name = f"{provider.consumer}"

        has_diff = False

        for field in fields:
            last_version = get_last_version(
                self.consumer_type, instance.pk, field)

            if last_version > 0:
                diffs = Diff.objects.filter(
                    action__consumer_type=self.consumer_type,
                    action__consumer_pk=instance.pk, field=field,
                    version=last_version)
                if len(diffs) > 1:
                    for diff in diffs[1:]:
                        diff.delete()
                last_diff = diffs[0]
                last_value = last_diff.get_version_text()

            else:
                last_value = ''

            new_value = utils.to_string(getattr(instance, field))

            if last_value != new_value:
                try:
                    last_action = Action.objects.filter(
                        diff__version=last_version, diff__field=field,
                        consumer_type=self.consumer_type,
                        consumer_pk=instance.pk).first()
                    if last_action:
                        last_date = last_action.created_at
                    else:
                        last_date = ''
                except IndexError as e:
                    logger.warning("Last action: {}".format(e))
                    last_date = ''
                    last_value = ''

                patch = '\n'.join(difflib.unified_diff(
                    last_value.splitlines(), new_value.splitlines(),
                    consumer_name, consumer_name,
                    str(last_date), str(provider.created_at),
                    lineterm=''))

                if patch:
                    has_diff = True
                else:
                    continue

                new_version = last_version + 1

                if not Diff.objects.filter(
                    action__consumer_type=self.consumer_type,
                    action__consumer_pk=instance.pk, field=field,
                    version=new_version).exists():

                    diff = Diff.objects.create(
                        action=provider, version=new_version, field=field,
                        change=patch)
                    diff.get_version_text()

        if not has_diff and action_type == defaults.ACTION_EDIT:
            provider.delete()


def object_m2m_save(sender, **kwargs):
    sender_name = f"{sender._meta.app_label}.{sender._meta.object_name.split('_')[0]}"
    try:
        consumer_type = ContentType.objects.get(
            app_label=sender._meta.app_label,
            model=sender._meta.object_name.split('_')[0].lower()
        )
    except Exception as e:
        logger.error(f"Content Type not found: {e}")
        return

    CreateDiff(
        sender_name, consumer_type, instance=kwargs.get('instance'), created=kwargs.get('created'),
        profile=get_current_user(), ip=get_current_ip()
    ).start()


def object_post_save(sender, **kwargs):
    sender_name = f"{sender._meta.app_label}.{sender._meta.object_name}"

    try:
        consumer_type = ContentType.objects.get_for_model(sender)
    except Exception as e:
        logger.error(f"Content Type not found: {e}")
        return

    CreateDiff(
        sender_name, consumer_type, instance=kwargs.get('instance'), created=kwargs.get('created'),
        profile=get_current_user(), ip=get_current_ip()
    ).start()


def object_pre_delete(sender, **kwargs):
    sender_name = '.'.join((sender._meta.app_label, sender._meta.object_name))
    if (
        (sender_name in defaults.OBSERVED_FIELDS) or
        utils.is_observed(sender_name, defaults.ACTION_DELETE)):
        instance = kwargs.get('instance')
        Action.objects.create(
            consumer_type=ContentType.objects.get_for_model(sender),
            consumer_pk=instance.pk, action_type=defaults.ACTION_DELETE,
            profile=get_current_user(), ip=get_current_ip())
