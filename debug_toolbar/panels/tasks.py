import django
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar.panels import Panel


class TasksPanel(Panel):
    """
    Panel that displays Django tasks queued or executed during the
    processing of the request.
    """

    title = _("Tasks")
    template = "debug_toolbar/panels/tasks.html"

    is_async = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queued_tasks = []

    @property
    def nav_subtitle(self):
        num_tasks = self.get_stats()["total_tasks"]
        return ngettext(
            "%(num_tasks)d task enqueued",
            "%(num_tasks)d tasks enqueued",
            num_tasks,
        ) % {"num_tasks": num_tasks}

    def generate_stats(self, request, response):
        stats = {"tasks": self.queued_tasks, "total_tasks": len(self.queued_tasks)}

        self.record_stats(stats)

    def enable_instrumentation(self):
        """Hook into task system to collect queued tasks"""
        if self._tasks_available is False:
            # Django tasks not available means that we cannot instrument
            return
        from django.tasks import Task

        print("[TasksPanel] instrumentation enabled:", hasattr(Task, "enqueue"))

        # Store original enqueue method
        if hasattr(Task, "enqueue"):
            self._original_enqueue = Task.enqueue

            def wrapped_enqueue(task, *args, **kwargs):
                result = self._original_enqueue(task, *args, **kwargs).return_value
                self._record_task(task, args, kwargs, result)
                return result

            Task.enqueue = wrapped_enqueue

    def _record_task(self, task, args, kwargs, result):
        """Record a task that was queued"""
        task_info = {
            "name": getattr(task, "__name__", str(task)),
            "args": repr(args) if args else "",
            "kwargs": repr(kwargs) if kwargs else "",
        }
        self.queued_tasks.append(task_info)

    def disable_instrumentation(self):
        """Restore original methods"""
        try:
            from django.tasks import Task

            if hasattr(self, "_original_enqueue"):
                Task.enqueue = self._original_enqueue
        except (ImportError, AttributeError):
            pass

    @property
    def _tasks_available(self) -> bool:
        """Check if Django tasks system is available"""
        if django.VERSION < (6, 0):
            return False
        return True
