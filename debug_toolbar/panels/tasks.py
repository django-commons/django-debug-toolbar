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
        pass

    def disable_instrumentation(self):
        pass
