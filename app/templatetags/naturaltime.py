import re
from datetime import date, datetime
from decimal import Decimal

from django import template
from django.conf import settings
from django.template import defaultfilters
from django.utils.formats import number_format
from django.utils.safestring import mark_safe
from django.utils.timezone import is_aware, utc
from django.utils.translation import gettext as _
from django.utils.translation import (gettext_lazy, ngettext, ngettext_lazy,
                                      npgettext_lazy, pgettext)

register = template.Library()

# Overwritten from django.contrib.humanize to leave only first part of timesince. (eg. 2 days, 5 hours ago -> 2 days ago)
# This filter doesn't require expects_localtime=True because it deals properly
# with both naive and aware datetimes. Therefore avoid the cost of conversion.
@register.filter
def naturaltime(value):
    """
    For date and time values show how many seconds, minutes, or hours ago
    compared to current timestamp return representing string.
    """
    return NaturalTimeFormatter.string_for(value)


class NaturalTimeFormatter:
    time_strings = {
        # Translators: delta will contain a string like '2 months' or '1 month, 2 weeks'
        'past-day': gettext_lazy('%(delta)s ago'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'past-hour': ngettext_lazy('an hour ago', '%(count)s hours ago', 'count'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'past-minute': ngettext_lazy('a minute ago', '%(count)s minutes ago', 'count'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'past-second': ngettext_lazy('a second ago', '%(count)s seconds ago', 'count'),
        'now': gettext_lazy('now'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'future-second': ngettext_lazy('a second from now', '%(count)s seconds from now', 'count'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'future-minute': ngettext_lazy('a minute from now', '%(count)s minutes from now', 'count'),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        'future-hour': ngettext_lazy('an hour from now', '%(count)s hours from now', 'count'),
        # Translators: delta will contain a string like '2 months' or '1 month, 2 weeks'
        'future-day': gettext_lazy('%(delta)s from now'),
    }
    past_substrings = {
        # Translators: 'naturaltime-past' strings will be included in '%(delta)s ago'
        'year': npgettext_lazy('naturaltime-past', '%d year', '%d years'),
        'month': npgettext_lazy('naturaltime-past', '%d month', '%d months'),
        'week': npgettext_lazy('naturaltime-past', '%d week', '%d weeks'),
        'day': npgettext_lazy('naturaltime-past', '%d day', '%d days'),
        'hour': npgettext_lazy('naturaltime-past', '%d hour', '%d hours'),
        'minute': npgettext_lazy('naturaltime-past', '%d minute', '%d minutes'),
    }
    future_substrings = {
        # Translators: 'naturaltime-future' strings will be included in '%(delta)s from now'
        'year': npgettext_lazy('naturaltime-future', '%d year', '%d years'),
        'month': npgettext_lazy('naturaltime-future', '%d month', '%d months'),
        'week': npgettext_lazy('naturaltime-future', '%d week', '%d weeks'),
        'day': npgettext_lazy('naturaltime-future', '%d day', '%d days'),
        'hour': npgettext_lazy('naturaltime-future', '%d hour', '%d hours'),
        'minute': npgettext_lazy('naturaltime-future', '%d minute', '%d minutes'),
    }

    @classmethod
    def string_for(cls, value):
        if not isinstance(value, date):  # datetime is a subclass of date
            return value

        now = datetime.now(utc if is_aware(value) else None)
        if value < now:
            delta = now - value
            if delta.days != 0:
                # The only change being done is here and in the else clausule:
                # It splits the string returned by timesince filter and gets only first element
                # to shorten the string so e.g '1 days, 5 hours' becomes '1 days'
                return cls.time_strings['past-day'] % {
                    'delta': defaultfilters.timesince(value, now, time_strings=cls.past_substrings).split(',')[0],
                }
            elif delta.seconds == 0:
                return cls.time_strings['now']
            elif delta.seconds < 60:
                return cls.time_strings['past-second'] % {'count': delta.seconds}
            elif delta.seconds // 60 < 60:
                count = delta.seconds // 60
                return cls.time_strings['past-minute'] % {'count': count}
            else:
                count = delta.seconds // 60 // 60
                return cls.time_strings['past-hour'] % {'count': count}
        else:
            delta = value - now
            if delta.days != 0:
                return cls.time_strings['future-day'] % {
                    'delta': defaultfilters.timeuntil(value, now, time_strings=cls.future_substrings).split(',')[0],
                }
            elif delta.seconds == 0:
                return cls.time_strings['now']
            elif delta.seconds < 60:
                return cls.time_strings['future-second'] % {'count': delta.seconds}
            elif delta.seconds // 60 < 60:
                count = delta.seconds // 60
                return cls.time_strings['future-minute'] % {'count': count}
            else:
                count = delta.seconds // 60 // 60
                return cls.time_strings['future-hour'] % {'count': count}
