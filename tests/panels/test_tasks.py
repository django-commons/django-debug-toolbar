import unittest
from unittest import mock

from debug_toolbar.panels.tasks import TasksPanel

from ..base import BaseTestCase

try:
    from django.tasks import task
except ImportError:
    task = None


if task is not None:

    @task
    def sample_task(x, y=1):
        return x + y


class TasksPanelTestCase(BaseTestCase):
    panel_id = TasksPanel.panel_id

    def test_nav_subtitle_without_tasks_support(self):
        """
        On Django < 6.0, django.tasks doesn't exist, so the panel should
        explain that instead of showing task data.
        """
        with mock.patch("debug_toolbar.panels.tasks.task_enqueued", None):
            self.panel.generate_stats(self.request, None)
            self.assertEqual(str(self.panel.nav_subtitle), "Requires Django 6.0+")
            stats = self.panel.get_stats()
            self.assertFalse(stats["tasks_available"])
            self.assertEqual(stats["tasks"], [])

    @unittest.skipUnless(task is not None, "Requires Django 6.0+")
    def test_no_tasks_queued(self):
        self.panel.generate_stats(self.request, None)
        stats = self.panel.get_stats()
        self.assertTrue(stats["tasks_available"])
        self.assertEqual(stats["tasks"], [])
        self.assertEqual(str(self.panel.nav_subtitle), "0 tasks")

    @unittest.skipUnless(task is not None, "Requires Django 6.0+")
    def test_records_queued_task(self):
        sample_task.enqueue(2, y=3)

        self.panel.generate_stats(self.request, None)
        stats = self.panel.get_stats()

        self.assertTrue(stats["tasks_available"])
        self.assertEqual(len(stats["tasks"]), 1)

        recorded = stats["tasks"][0]
        self.assertEqual(recorded["name"], f"{__name__}.sample_task")
        self.assertEqual(list(recorded["args"]), [2])
        self.assertEqual(dict(recorded["kwargs"]), {"y": 3})
        self.assertEqual(recorded["queue_name"], "default")
        self.assertEqual(recorded["backend"], "default")

    @unittest.skipUnless(task is not None, "Requires Django 6.0+")
    def test_nav_subtitle_counts_multiple_tasks(self):
        sample_task.enqueue(1)
        sample_task.enqueue(2)

        self.panel.generate_stats(self.request, None)

        self.assertEqual(str(self.panel.nav_subtitle), "2 tasks")

    @unittest.skipUnless(task is not None, "Requires Django 6.0+")
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
