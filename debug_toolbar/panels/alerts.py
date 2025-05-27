from html.parser import HTMLParser

from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.utils import is_processable_html_response


class FormParser(HTMLParser):
    """
    HTML form parser, used to check for invalid configurations of forms that
    take file inputs.
    """

    def __init__(self):
        super().__init__()
        self.in_form = False
        self.current_form = {}
        self.forms = []
        self.form_ids = []
        self.referenced_file_inputs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.in_form = True
            form_id = attrs.get("id")
            if form_id:
                self.form_ids.append(form_id)
            self.current_form = {
                "file_form": False,
                "form_attrs": attrs,
                "submit_element_attrs": [],
            }
        elif (
            self.in_form
            and tag == "input"
            and attrs.get("type") == "file"
            and (not attrs.get("form") or attrs.get("form") == "")
        ):
            self.current_form["file_form"] = True
        elif (
            self.in_form
            and (
                (tag == "input" and attrs.get("type") in {"submit", "image"})
                or tag == "button"
            )
            and (not attrs.get("form") or attrs.get("form") == "")
        ):
            self.current_form["submit_element_attrs"].append(attrs)
        elif tag == "input" and attrs.get("form"):
            self.referenced_file_inputs.append(attrs)

    def handle_endtag(self, tag):
        if tag == "form" and self.in_form:
            self.forms.append(self.current_form)
            self.in_form = False


class AlertsPanel(Panel):
    """
    A panel to alert users to issues.
    """

    messages = {
        "form_id_missing_enctype": _(
            'Form with id "{form_id}" contains file input, but does not have the attribute enctype="multipart/form-data".'
        ),
        "form_missing_enctype": _(
            'Form contains file input, but does not have the attribute enctype="multipart/form-data".'
        ),
        "input_refs_form_missing_enctype": _(
            'Input element references form with id "{form_id}", but the form does not have the attribute enctype="multipart/form-data".'
        ),
    }

    title = _("Alerts")

    is_async = True

    template = "debug_toolbar/panels/alerts.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alerts = []

    @property
    def nav_subtitle(self):
        if alerts := self.get_stats().get("alerts"):
            alert_text = "alert" if len(alerts) == 1 else "alerts"
            return f"{len(alerts)} {alert_text}"
        else:
            return ""

    def add_alert(self, alert):
        self.alerts.append(alert)

    def check_invalid_file_form_configuration(self, html_content):
        """
        Inspects HTML content for a form that includes a file input but does
        not have the encoding type set to multipart/form-data, and warns the
        user if so.
        """
        parser = FormParser()
        parser.feed(html_content)

        # Check for file inputs directly inside a form that do not reference
        # any form through the form attribute
        for form in parser.forms:
            if (
                form["file_form"]
                and form["form_attrs"].get("enctype") != "multipart/form-data"
                and not any(
                    elem.get("formenctype") == "multipart/form-data"
                    for elem in form["submit_element_attrs"]
                )
            ):
                if form_id := form["form_attrs"].get("id"):
                    alert = self.messages["form_id_missing_enctype"].format(
                        form_id=form_id
                    )
                else:
                    alert = self.messages["form_missing_enctype"]
                self.add_alert({"alert": alert})

        # Check for file inputs that reference a form
        form_attrs_by_id = {
            form["form_attrs"].get("id"): form["form_attrs"] for form in parser.forms
        }

        for attrs in parser.referenced_file_inputs:
            form_id = attrs.get("form")
            if form_id and attrs.get("type") == "file":
                form_attrs = form_attrs_by_id.get(form_id)
                if form_attrs and form_attrs.get("enctype") != "multipart/form-data":
                    alert = self.messages["input_refs_form_missing_enctype"].format(
                        form_id=form_id
                    )
                    self.add_alert({"alert": alert})

        return self.alerts

    def generate_stats(self, request, response):
        if is_processable_html_response(response):
            html_content = response.content.decode(response.charset)
            self.check_invalid_file_form_configuration(html_content)

        # Further alert checks can go here

        # Write all alerts to record_stats
        self.record_stats({"alerts": self.alerts})
