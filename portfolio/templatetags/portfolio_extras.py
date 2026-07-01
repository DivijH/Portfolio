from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def split(value, sep=','):
    """Split a string into a stripped list, dropping empties."""
    return [p.strip() for p in (value or '').split(sep) if p.strip()]


@register.filter
def highlight_author(authors, name):
    """Bold the site owner's name within a comma-separated author string."""
    authors = conditional_escape(authors or '')
    name = (name or '').strip()
    if name:
        escaped = conditional_escape(name)
        authors = authors.replace(escaped, f'<span class="me">{escaped}</span>')
        # Also catch a 'Lastname, F.'-free common case: last name only.
        last = name.split()[-1]
        if last and last != name:
            esc_last = conditional_escape(last)
            if f'<span class="me">' not in authors:
                authors = authors.replace(esc_last, f'<span class="me">{esc_last}</span>')
    return mark_safe(authors)
