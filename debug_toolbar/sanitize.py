from django.utils.encoding import DjangoUnicodeDecodeError, force_str as force_string


def force_str(s, *args, **kwargs):
    """
    Forces values to strings.
    Will return "Django Debug Toolbar was unable to parse value." when there's a decoding error.
    """
    try:
        return force_string(s, *args, **kwargs)
    except DjangoUnicodeDecodeError:
        return "Django Debug Toolbar was unable to parse value."
