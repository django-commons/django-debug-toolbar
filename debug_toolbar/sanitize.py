from django.utils.encoding import DjangoUnicodeDecodeError, force_str as force_string


def force_str(force_function, value):
    try:
        return force_string(value)
    except DjangoUnicodeDecodeError:
        return "Django Debug Toolbar was unable to parse value."
