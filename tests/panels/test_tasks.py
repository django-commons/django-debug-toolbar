import unittest

from debug_toolbar._compat import django_has_tasks_support, task
from debug_toolbar.panels.tasks import TasksPanel

from ..base import BaseTestCase


@task
def sample_task(x, y=1):
    return x + y


class TasksPanelTestCase(BaseTestCase):
    panel_id = TasksPanel.panel_id

    @unittest.skipUnless(not django_has_tasks_support, "Requires Django < 6.0")
    def test_nav_subtitle_without_tasks_support(self):
        """
        On Django < 6.0, django.tasks doesn't exist, so the panel should
        explain that instead of showing task data.
        """
        self.panel.generate_stats(self.request, None)
        self.assertEqual(str(self.panel.nav_subtitle), "Requires Django 6.0+")
        stats = self.panel.get_stats()
        self.assertEqual(stats, {"tasks_available": False, "tasks": []})

    @unittest.skipUnless(django_has_tasks_support, "Requires Django 6.0+")
    def test_no_tasks_queued(self):
        self.panel.generate_stats(self.request, None)
        stats = self.panel.get_stats()
        self.assertEqual(stats, {"tasks_available": True, "tasks": []})
        self.assertEqual(str(self.panel.nav_subtitle), "0 tasks")

    @unittest.skipUnless(django_has_tasks_support, "Requires Django 6.0+")
    def test_records_queued_task(self):
        sample_task.enqueue(2, y=3)

        self.panel.generate_stats(self.request, None)
        stats = self.panel.get_stats()
        self.assertEqual(len(stats["tasks"]), 1)

        # id, priority, run_after, and status are runtime-dependent, so
        # pull them from the actual result and assert the rest of the
        # dict matches exactly around them.
        recorded = stats["tasks"][0]
        self.assertEqual(
            stats,
            {
                "tasks_available": True,
                "tasks": [
                    {
                        "id": recorded["id"],
                        "name": f"{__name__}.sample_task",
                        "queue_name": "default",
                        "priority": recorded["priority"],
                        "backend": "default",
                        "run_after": recorded["run_after"],
                        "takes_context": False,
                        "args": {"raw": [2]},
                        "kwargs": {"list": [("y", 3)]},
                        "status": recorded["status"],
                    }
                ],
            },
        )

    @unittest.skipUnless(django_has_tasks_support, "Requires Django 6.0+")
    def test_nav_subtitle_counts_multiple_tasks(self):
        sample_task.enqueue(1)
        sample_task.enqueue(2)

        self.panel.generate_stats(self.request, None)

        self.assertEqual(str(self.panel.nav_subtitle), "2 tasks")

    @unittest.skipUnless(django_has_tasks_support, "Requires Django 6.0+")
    def test_disable_instrumentation_stops_recording(self):
        self.panel.disable_instrumentation()
        try:
            sample_task.enqueue(1)
        finally:
            # Restore instrumentation so tearDown's disable call is a no-op
            # rather than raising for double-disconnecting.
            self.panel.enable_instrumentation()

        self.panel.generate_stats(self.request, None)
        stats = self.panel.get_stats()
        self.assertEqual(stats["tasks"], [])
