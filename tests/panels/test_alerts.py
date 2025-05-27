from django.http import HttpResponse, StreamingHttpResponse
from django.template import Context, Template

from ..base import BaseTestCase


class AlertsPanelTestCase(BaseTestCase):
    panel_id = "AlertsPanel"

    def test_alert_warning_display(self):
        """
        Test that the panel (does not) display[s] an alert when there are
        (no) problems.
        """
        self.panel.record_stats({"alerts": []})
        self.assertNotIn("alerts", self.panel.nav_subtitle)

        self.panel.record_stats({"alerts": ["Alert 1", "Alert 2"]})
        self.assertIn("2 alerts", self.panel.nav_subtitle)

    def test_file_form_without_enctype_multipart_form_data(self):
        """
        Test that the panel displays a form invalid message when there is
        a file input but encoding not set to multipart/form-data.
        """
        test_form = '<form id="test-form"><input type="file"></form>'
        result = self.panel.check_invalid_file_form_configuration(test_form)
        expected_error = (
            'Form with id "test-form" contains file input, '
            'but does not have the attribute enctype="multipart/form-data".'
        )
        self.assertEqual(result[0]["alert"], expected_error)
        self.assertEqual(len(result), 1)

    def test_file_form_no_id_without_enctype_multipart_form_data(self):
        """
        Test that the panel displays a form invalid message when there is
        a file input but encoding not set to multipart/form-data.

        This should use the message when the form has no id.
        """
        test_form = '<form><input type="file"></form>'
        result = self.panel.check_invalid_file_form_configuration(test_form)
        expected_error = (
            "Form contains file input, but does not have "
            'the attribute enctype="multipart/form-data".'
        )
        self.assertEqual(result[0]["alert"], expected_error)
        self.assertEqual(len(result), 1)

    def test_file_form_with_enctype_multipart_form_data(self):
        test_form = """<form id="test-form" enctype="multipart/form-data">
        <input type="file">
        </form>"""
        result = self.panel.check_invalid_file_form_configuration(test_form)

        self.assertEqual(len(result), 0)

    def test_file_form_with_enctype_multipart_form_data_in_button(self):
        test_form = """<form id="test-form">
        <input type="file">
        <input type="submit" formenctype="multipart/form-data">
        </form>"""
        result = self.panel.check_invalid_file_form_configuration(test_form)

        self.assertEqual(len(result), 0)

    def test_referenced_file_input_without_enctype_multipart_form_data(self):
        test_file_input = """<form id="test-form"></form>
        <input type="file" form = "test-form">"""
        result = self.panel.check_invalid_file_form_configuration(test_file_input)

        expected_error = (
            'Input element references form with id "test-form", '
            'but the form does not have the attribute enctype="multipart/form-data".'
        )
        self.assertEqual(result[0]["alert"], expected_error)
        self.assertEqual(len(result), 1)

    def test_referenced_file_input_with_enctype_multipart_form_data(self):
        test_file_input = """<form id="test-form" enctype="multipart/form-data">
        </form>
        <input type="file" form = "test-form">"""
        result = self.panel.check_invalid_file_form_configuration(test_file_input)

        self.assertEqual(len(result), 0)

    def test_integration_file_form_without_enctype_multipart_form_data(self):
        t = Template('<form id="test-form"><input type="file"></form>')
        c = Context({})
        rendered_template = t.render(c)
        response = HttpResponse(content=rendered_template)

        self.panel.generate_stats(self.request, response)

        self.assertIn("1 alert", self.panel.nav_subtitle)
        self.assertIn(
            "Form with id &quot;test-form&quot; contains file input, "
            "but does not have the attribute enctype=&quot;multipart/form-data&quot;.",
            self.panel.content,
        )

    def test_streaming_response(self):
        """Test to check for a streaming response."""

        def _render():
            yield "ok"

        response = StreamingHttpResponse(_render())

        self.panel.generate_stats(self.request, response)
        self.assertEqual(self.panel.get_stats(), {"alerts": []})
