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

        self.assertEqual(stats.keys(), {"tasks_available", "tasks"})
        self.assertEqual(stats["tasks_available"], True)
        self.assertEqual(len(stats["tasks"]), 1)
        task_result = stats["tasks"][0]
        self.assertEqual(task_result["task"]["module_path"], f"{__name__}.sample_task")
        self.assertEqual(task_result["task"]["queue_name"], "default")
        self.assertEqual(task_result["task"]["priority"], 0)
        self.assertEqual(task_result["backend"], "default")
        self.assertEqual(task_result["task"]["run_after"], None)
        self.assertEqual(task_result["args"], [2])
        self.assertEqual(task_result["kwargs"], {"y": 3})
        self.assertEqual(task_result["status"], "SUCCESSFUL")

    @unittest.skipUnless(django_has_tasks_support, "Requires Django 6.0+")
    def test_records_queued_task_rendered_in_template(self):
        """Test the Tasks panel's rendered html.

        Since the template for the panel contains the logic for which properties
        are accessed to render the content, we should validate the properties
        explicitly rather than solely relying on test_records_queued_task
        confirming the shape.
        """
        sample_task.enqueue(2, y=3)

        self.panel.generate_stats(self.request, None)
        # This round-trips through the store rather than reading the
        # panel's in-memory stats.
        self.reload_stats()
        content = self.panel.content

        # task.task.module_path
        self.assertIn(f"{__name__}.sample_task", content)
        # task.task.queue_name / task.backend
        self.assertIn("default", content)
        # task.task.priority
        self.assertIn("0", content)
        # task.status
        self.assertIn("SUCCESSFUL", content)
        # task.args
        self.assertIn("[2]", content)
        # task.kwargs
        self.assertIn("{&#x27;y&#x27;: 3}", content)
        self.assertValidHTML(content)

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
