from django.utils.encoding import DjangoUnicodeDecodeError, force_str as force_string


# def force_str(s, encoding="utf-8", strings_only=False, errors="strict"):
#     try:
#         return force_string(s, encoding, strings_only, errors)
#     except DjangoUnicodeDecodeError:
#         return "Django Debug Toolbar was unable to parse value."

def force_str(s, *args, **kwargs):
    try:
        return force_string(s, *args, **kwargs)
    except DjangoUnicodeDecodeError:
        return "Django Debug Toolbar was unable to parse value."
