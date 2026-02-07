from django import template

register = template.Library()


@register.filter
def int_to_letter(value):
    """Convert an integer (0-based) to a lowercase letter (a, b, c, ...)"""
    if isinstance(value, int) and value >= 0:
        return chr(value + 97)  # 97 is ASCII for 'a'
    return ""
