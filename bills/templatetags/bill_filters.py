from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def floordiv(value, arg):
    """Integer division of the value by the argument"""
    try:
        return int(float(value) // float(arg))
    except (ValueError, TypeError):
        return value 