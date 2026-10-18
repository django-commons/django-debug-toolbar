import django

try:
    from django.contrib.auth.decorators import login_not_required
except ImportError:
    # For Django < 5.1, copy the current Django implementation
    def login_not_required(view_func):
        """
        Decorator for views that allows access to unauthenticated requests.
        """
        view_func.login_required = False
        return view_func


if django.VERSION >= (6, 0):
    from django.middleware.csp import get_nonce
else:
    # For Django < 6.0, there is no native CSP support, hence no CSP nonces.
    def get_nonce(request):
        return None


# django.tasks was added in Django 6.0.
django_has_tasks_support = django.VERSION >= (6, 0)

if django_has_tasks_support:
    from django.tasks import task
else:
    # For Django < 6.0, django.tasks doesn't exist. This pass-through
    # decorator lets call sites decorate funtcions unconditionally
    # tests that need real task behavior should use
    # @skipUnless(django_has_tasks_support, ...) instead of relying on
    # this decorator doing anything useful.
    def task(func=None, **kwargs):
        if func is None:
            return lambda f: f
        return func
