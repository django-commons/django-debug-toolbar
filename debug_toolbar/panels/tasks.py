from django import VERSION
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar.panels import Panel

if VERSION >= (6, 0):
    from django.tasks.signals import task_enqueued
else:
    task_enqueued = None


class TasksPanel(Panel):
    """
    Panel that displays the tasks queued during the request.

    This relies on Django's built-in tasks framework (``django.tasks``),
    which was added in Django 6.0. On older versions of Django, the panel
    explains that upgrading Django is required in order to see task
    information.
    """

    template = "debug_toolbar/panels/tasks.html"

    is_async = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = []

    # Implement the Panel API

    nav_title = _("tasks")

    @property
    def nav_subtitle(self):
        if VERSION < (6, 0):
            return _("Requires Django 6.0+")
        tasks = self.get_stats()["tasks"]
        return ngettext("%(count)d task", "%(count)d tasks", len(tasks)) % {
            "count": len(tasks)
        }

    title = _("tasks")

    def _record_task(self, sender, task_result, **kwargs):
        self.tasks.append(task_result)

    def enable_instrumentation(self):
        if task_enqueued is not None:
            task_enqueued.connect(self._record_task)

    def disable_instrumentation(self):
        if task_enqueued is not None:
            task_enqueued.disconnect(self._record_task)

    def generate_stats(self, request, response):
        self.record_stats(
            {
                "tasks_available": VERSION >= (6, 0),
                "tasks": self.tasks,
            }
        )
