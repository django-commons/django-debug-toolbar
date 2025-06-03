import json

from django import forms
from django.core.exceptions import ValidationError
from django.db import connections
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels.sql.utils import is_select_query, reformat_sql
from debug_toolbar.toolbar import DebugToolbar


class SQLSelectForm(forms.Form):
    """
    Validate params

        request_id: The identifier for the request
        query_id: The identifier for the query
    """

    request_id = forms.CharField()
    djdt_query_id = forms.CharField()

    def clean_raw_sql(self):
        value = self.cleaned_data["raw_sql"]

        if not is_select_query(value):
            raise ValidationError("Only 'select' queries are allowed.")

        return value

    def clean_params(self):
        value = self.cleaned_data["params"]

        try:
            return json.loads(value)
        except ValueError as exc:
            raise ValidationError("Is not valid JSON") from exc

    def clean_alias(self):
        value = self.cleaned_data["alias"]

        if value not in connections:
            raise ValidationError(f"Database alias '{value}' not found")

        return value

    def clean(self):
        from debug_toolbar.panels.sql import SQLPanel

        cleaned_data = super().clean()
        toolbar = DebugToolbar.fetch(
            self.cleaned_data["request_id"], panel_id=SQLPanel.panel_id
        )
        if toolbar is None:
            raise ValidationError(_("Data for this panel isn't available anymore."))

        panel = toolbar.get_panel_by_id(SQLPanel.panel_id)
        # Find the query for this form submission
        query = None
        for q in panel.get_stats()["queries"]:
            if q["djdt_query_id"] != self.cleaned_data["djdt_query_id"]:
                continue
            else:
                query = q
                break
        if not query:
            raise ValidationError(_("Invalid query id."))
        cleaned_data["query"] = query
        return cleaned_data

    def select(self):
        query = self.cleaned_data["query"]
        sql = query["raw_sql"]
        params = json.loads(query["params"])
        with self.cursor as cursor:
            cursor.execute(sql, params)
            headers = [d[0] for d in cursor.description]
            result = cursor.fetchall()
            return result, headers

    def explain(self):
        query = self.cleaned_data["query"]
        sql = query["raw_sql"]
        params = json.loads(query["params"])
        vendor = query["vendor"]
        with self.cursor as cursor:
            if vendor == "sqlite":
                # SQLite's EXPLAIN dumps the low-level opcodes generated for a query;
                # EXPLAIN QUERY PLAN dumps a more human-readable summary
                # See https://www.sqlite.org/lang_explain.html for details
                cursor.execute(f"EXPLAIN QUERY PLAN {sql}", params)
            elif vendor == "postgresql":
                cursor.execute(f"EXPLAIN ANALYZE {sql}", params)
            else:
                cursor.execute(f"EXPLAIN {sql}", params)
            headers = [d[0] for d in cursor.description]
            result = cursor.fetchall()
            return result, headers

    def profile(self):
        query = self.cleaned_data["query"]
        sql = query["raw_sql"]
        params = json.loads(query["params"])
        with self.cursor as cursor:
            cursor.execute("SET PROFILING=1")  # Enable profiling
            cursor.execute(sql, params)  # Execute SELECT
            cursor.execute("SET PROFILING=0")  # Disable profiling
            # The Query ID should always be 1 here but I'll subselect to get
            # the last one just in case...
            cursor.execute(
                """
                SELECT *
                FROM information_schema.profiling
                WHERE query_id = (
                    SELECT query_id
                    FROM information_schema.profiling
                    ORDER BY query_id DESC
                    LIMIT 1
                )
                """
            )
            headers = [d[0] for d in cursor.description]
            result = cursor.fetchall()
            return result, headers

    def reformat_sql(self):
        return reformat_sql(self.cleaned_data["query"]["sql"], with_toggle=False)

    @property
    def connection(self):
        return connections[self.cleaned_data["query"]["alias"]]

    @cached_property
    def cursor(self):
        return self.connection.cursor()
