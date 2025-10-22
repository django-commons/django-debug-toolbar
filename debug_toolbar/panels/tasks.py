from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel


class TasksPanel(Panel):
    """
    Panel that displays Django tasks queued or executed during the
    processing of the request.
    """

    title = _("Tasks")
    template = "debug_toolbar/panels/tasks.html"

    is_async = True
