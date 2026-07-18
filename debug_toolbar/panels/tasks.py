from django import VERSION
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar.panels import Panel
from debug_toolbar.utils import sanitize_and_sort_request_vars

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

    nav_title = _("Tasks")

    @property
    def nav_subtitle(self):
        if VERSION < (6, 0):
            return _("Requires Django 6.0+")
        tasks = self.get_stats()["tasks"]
        return ngettext("%(count)d task", "%(count)d tasks", len(tasks)) % {
            "count": len(tasks)
        }

    title = _("Tasks")

    def _record_task(self, sender, task_result, **kwargs):
        # Panel stats get JSON-serialized for the history panel and async
        # requests (see debug_toolbar/store.py), so we can't store the
        # TaskResult dataclass directly: it holds a raw function reference
        # (Task.func) that isn't JSON-serializable, and would silently
        # collapse into an opaque repr string on the round-trip. Instead we
        # mirror TaskResult's own field names/values one to one, only
        # dropping non-serializable internals and sanitizing args/kwargs.
        task = task_result.task
        self.tasks.append(
            {
                "id": task_result.id,
                "module_path": task.module_path,
                "queue_name": task.queue_name,
                "priority": task.priority,
                "backend": task_result.backend,
                "run_after": task.run_after,
                "takes_context": task.takes_context,
                "args": sanitize_and_sort_request_vars(task_result.args),
                "kwargs": sanitize_and_sort_request_vars(task_result.kwargs),
                "status": task_result.status,
            }
        )

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
