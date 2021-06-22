import datetime
import re
from django.db.models import Model, Q

HUNK_RE = '@@ \-(\d+)(,(\d+))? \+(\d+)(,(\d+))? @@'


def merge(diffs):
    """
    Apply multiple diffs.
    Add one line:
    >>> merge([
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,0 +1,1 @@\\n'
    ...     '+qwf'])
    u'qwf'
    Remove one line:
    >>> merge([
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,0 +1,1 @@\\n'
    ...     '+qwf\\n',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,1 +1,0 @@\\n'
    ...     '-qwf'])
    u''
    Replace one line:
    >>> merge([
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,0 +1,2 @@\\n'
    ...     '+qwf\\n'
    ...     '+zxc\\n',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,2 +1,2 @@\\n'
    ...     ' qwf\\n'
    ...     '-zxc\\n'
    ...     '+ars'])
    u'qwf\\nars'
    Mixed lines, multiple hunks:
    1234 -> 123456 -> 1357 -> 1839507abcd -> 893507abc
    >>> merge([
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,0 +1,4 @@\\n'
    ...     '+11\\n'
    ...     '+22\\n'
    ...     '+33\\n'
    ...     '+44',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -2,3 +2,5 @@\\n'
    ...     ' 22\\n'
    ...     ' 33\\n'
    ...     ' 44\\n'
    ...     '+55\\n'
    ...     '+66',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,6 +1,4 @@\\n'
    ...     ' 11\\n'
    ...     '-22\\n'
    ...     ' 33\\n'
    ...     '-44\\n'
    ...     ' 55\\n'
    ...     '-66\\n'
    ...     '+77',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,4 +1,11 @@\\n'
    ...     ' 11\\n'
    ...     '+88\\n'
    ...     ' 33\\n'
    ...     '+99\\n'
    ...     ' 55\\n'
    ...     '+00\\n'
    ...     ' 77\\n'
    ...     '+aa\\n'
    ...     '+bb\\n'
    ...     '+cc\\n'
    ...     '+dd',
    ...     '--- \\n'
    ...     '+++ \\n'
    ...     '@@ -1,4 +1,3 @@\\n'
    ...     '-11\\n'
    ...     ' 88\\n'
    ...     ' 33\\n'
    ...     ' 99\\n'
    ...     '@@ -8,4 +7,3 @@\\n'
    ...     ' aa\\n'
    ...     ' bb\\n'
    ...     ' cc\\n'
    ...     '-dd'])
    u'88\\n33\\n99\\n55\\n00\\n77\\naa\\nbb\\ncc'
    Test with real world data:
    >>> merge([
    ... '--- [2011/05/12 13:22] zz\\n'
    ... '+++ [2011/05/12 13:22] zz 2011-05-12 13:22:51.895911\\n'
    ... '@@ -1,0 +1,1 @@\\n'
    ... '+<p>qqZZZ</p>',
    ... '--- [2011/05/12 13:22] zz 2011-05-12 13:22:51.895911\\n'
    ... '+++ [2011/05/12 13:22] zz 2011-05-12 13:23:06.504037\\n'
    ... '@@ -1,1 +1,3 @@\\n'
    ... ' <p>qqZZZ</p>\\n'
    ... '+<p>12323arsar</p>\\n'
    ... '+<p>arsars</p>',
    ... '--- [2011/05/12 13:22] zz 2011-05-12 13:23:06.504037\\n'
    ... '+++ [2011/05/12 13:22] zz 2011-05-12 13:23:24.784658\\n'
    ... '@@ -1,3 +1,1 @@\\n'
    ... ' <p>qqZZZ</p>\\n'
    ... '-<p>12323arsar</p>\\n'
    ... '-<p>arsars</p>'])
    u'<p>qqZZZ</p>'
    """
    hunk_re = re.compile(HUNK_RE)
    text = []
    for diff in diffs:
        text_new = text[:]
        lines = (line for line in diff.splitlines())
        line = ''
        while line is not None:
            try:
                line = lines.__next__()
                if line.startswith('--- '):
                    lines.__next__()
                    line = lines.__next__()

                # Parse hunk info.
                match = hunk_re.match(line)
                if match is None:
                    continue

                (start_old, has_size_old, size_old, start_new, has_size_new,
                 size_new) = match.groups()

                if has_size_old is None:
                    size_old = 1

                if has_size_new is None:
                    size_new = 1

                start_old, size_old, start_new, size_new = map(
                    int, (start_old, size_old, start_new, size_new))

                start_old -= 1
                start_new -= 1

                # Parse hunk.
                end_new = start_new + size_new
                end_old = start_old + size_old
                while start_new < end_new or start_old < end_old:
                    line = lines.__next__()

                    if line.startswith('-'):
                        # Line removed.
                        assert text[start_old] == line[1:], \
                            "Deleted text didn't match: %s\n%s" % (
                                text, line)
                        del text_new[start_new]
                        start_old += 1
                    elif line.startswith('+'):
                        # Line added.
                        text_new.insert(start_new, line[1:])
                        start_new += 1

                    else:
                        # Line unchanged.
                        line = line[1:]
                        assert text[start_old] == text_new[start_new] == line, \
                            "Text shouldn't change here: %s\n%s" % (
                                diff, (text[start_old], line, text))
                        start_old += 1
                        start_new += 1
            except Exception as e:
                line = None
        text = text_new

    return u'\n'.join(line for line in text if line is not None)


def to_string(value):
    if callable(value):
        value = ', '.join([val.__str__() for val in value.all()])
        return str(value)
    if isinstance(value, datetime.datetime):
        return f"{value.strftime('%Y-%m-%d %H:%M')}"
    elif isinstance(value, datetime.date):
        return f"{value.strftime('%Y-%m-%d')}"
    elif isinstance(value, Model):
        return f"{value.pk} ({value})"
    elif isinstance(value, str):
        return f"{value}"
    else:
        return f"{value}"


def from_string(value, to_type):
    if value is 'None':
        return None

    elif to_type:
        return value
    elif issubclass(to_type, str):
        return value.encode('utf-8')
    elif issubclass(to_type, bool):
        return value == u'True'
    elif issubclass(to_type, int):
        return int(value)
    elif issubclass(to_type, datetime.datetime):
        return datetime.datetime.strptime(value, '%d/%m/%Y %H:%M')
    elif issubclass(to_type, Model):
        return to_type.objects.get(pk=value.split(' ', 1)[0])
    else:
        raise NotImplementedError


_TIMELINE_FIELDS_DATA = {}


def observe(
    model, create=False, edit=False, delete=False, rollback=False,
    rename=False):
    assert any((create, edit, delete, rollback, rename)), \
        "At least one action type must be set"
    _TIMELINE_FIELDS_DATA[model] = (create, edit, delete, rollback, rename)
    return model


def is_observed(model, event):
    model_data = _TIMELINE_FIELDS_DATA.get(model)
    if not model_data:
        return False

    return model_data[event]


def get_consumer_filter(key):
    from . import defaults
    action_types = [
        action_type for action_type, title in defaults.ACTION_TYPES
        if _TIMELINE_FIELDS_DATA[key][action_type]]
    app, model = key.split('.')
    return Q(
        Q(consumer_type__app_label=app) &
        Q(consumer_type__model=model.lower()) &
        Q(action_type__in=action_types))
