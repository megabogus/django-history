import itertools
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .utils import observe


(
    ACTION_CREATE, ACTION_EDIT, ACTION_DELETE, ACTION_ROLLBACK,
    ACTION_RENAME, ACTION_TRASH, ACTION_RESTORE
) = range(0, 7)

ACTION_TYPES = (
    (ACTION_CREATE, _('Созданный объект')),
    (ACTION_EDIT, _('Отредактированный объект')),
    (ACTION_DELETE, _('Удаленный объект')),
    (ACTION_ROLLBACK, _('отмена')),
    (ACTION_RENAME, _('Переименованный объект')),
    (ACTION_TRASH, _('Перемещено в корзину')),
    (ACTION_RESTORE, _('Восстановлен из корзины')),
)

OBSERVED_FIELDS = getattr(
    settings, 'OBSERVED_FIELDS',
    {
        'accounts.User':
            (
                'username', 'first_name', 'middle_name', 'last_name', 'gender', 'phone', 'email',
                'photo', 'birthday',
            ),
     })

OBSERVED_FIELD_NAMES = list(set(itertools.chain.from_iterable(OBSERVED_FIELDS.values())))

TIMELINE_PAGE_DAYS = getattr(settings, 'TIMELINE_PAGE_DAYS', 7)

AUTHORS_TOP_LIMIT = getattr(settings, 'AUTHORS_TOP_LIMIT', 10)

TIMELINE_FEED_DAYS = getattr(settings, 'TIMELINE_FEED_DAYS', 3)
