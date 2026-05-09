import cProfile
import logging
import os
from colorsys import hsv_to_rgb
from pstats import Stats

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from debug_toolbar import settings as dt_settings
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar
from debug_toolbar.panels import Panel
from debug_toolbar.toolbar import DebugToolbar
from debug_toolbar.utils import get_view_path_metadata

logger = logging.getLogger(__name__)


class FunctionCall:
    def __init__(
        self, statobj, func, depth=0, stats=None, id=0, parent_ids=None, hsv=(0, 0.5, 1)
    ):
        self.statobj = statobj
        self.func = func
        if stats:
            self.stats = stats
        else:
            self.stats = statobj.stats[func][:4]
        self.depth = depth
        self.id = id
        self.parent_ids = parent_ids or []
        self.hsv = hsv
        self.has_subfuncs = False

    def parent_classes(self):
        return self.parent_classes

    def background(self):
        r, g, b = hsv_to_rgb(*self.hsv)
        return f"rgb({r * 100:f}%,{g * 100:f}%,{b * 100:f}%)"

    def is_project_func(self):
        """
        Check if the function is from the project code.

        Project code is identified by the BASE_DIR setting
        which is used in Django projects by default.
        """
        if hasattr(settings, "BASE_DIR"):
            file_name, _, _ = self.func
            base_dir = str(settings.BASE_DIR)

            file_name = os.path.normpath(file_name)
            base_dir = os.path.normpath(base_dir)

            return file_name.startswith(base_dir) and not any(
                directory in file_name.split(os.path.sep)
                for directory in ["site-packages", "dist-packages"]
            )
        return None

    def func_std_string(self):  # match what old profile produced
        func_name = self.func
        if func_name[:2] == ("~", 0):
            # special case for built-in functions
            name = func_name[2]
            if name.startswith("<") and name.endswith(">"):
                return f"{{{name[1:-1]}}}"
            else:
                return name
        else:
            file_name, line_num, method = self.func
            idx = file_name.find("/site-packages/")
            if idx > -1:
                file_name = file_name[(idx + 14) :]

            split_path = file_name.rsplit(os.sep, 1)
            if len(split_path) > 1:
                file_path, file_name = file_name.rsplit(os.sep, 1)
            else:
                file_path = "<module>"

            return format_html(
                '<span class="djdt-path">{0}/</span>'
                '<span class="djdt-file">{1}</span>'
                ' in <span class="djdt-func">{3}</span>'
                '(<span class="djdt-lineno">{2}</span>)',
                file_path,
                file_name,
                line_num,
                method,
            )

    def subfuncs(self):
        h, s, v = self.hsv
        count = len(self.statobj.all_callees[self.func])
        for i, (func, stats) in enumerate(self.statobj.all_callees[self.func].items()):
            h1 = h + ((i + 1) / count) / (self.depth + 1)
            s1 = 0 if self.stats[3] == 0 else s * (stats[3] / self.stats[3])
            yield FunctionCall(
                self.statobj,
                func,
                self.depth + 1,
                stats=stats,
                id=str(self.id) + "_" + str(i),
                parent_ids=self.parent_ids + [self.id],
                hsv=(h1, s1, 1),
            )

    def count(self):
        return self.stats[1]

    def tottime(self):
        return self.stats[2]

    def cumtime(self):
        cc, nc, tt, ct = self.stats
        return self.stats[3]

    def tottime_per_call(self):
        cc, nc, tt, ct = self.stats

        if nc == 0:
            return 0

        return tt / nc

    def cumtime_per_call(self):
        cc, nc, tt, ct = self.stats

        if cc == 0:
            return 0

        return ct / cc

    def indent(self):
        return 16 * self.depth

    def primitive_count(self):
        return self.stats[0]

    def _func_key(self):
        # Mirrors pstats.func_std_string to produce the plain-text identifier
        # used in downloaded .prof files.
        # https://docs.python.org/3/library/profile.html#pstats.Stats
        if self.func[:2] == ("~", 0):
            name = self.func[2]
            if name.startswith("<") and name.endswith(">"):
                return f"{{{name[1:-1]}}}"
            return name
        return "%s:%d(%s)" % self.func

    def serialize(self):
        return {
            "has_subfuncs": self.has_subfuncs,
            "id": self.id,
            "parent_ids": self.parent_ids,
            "is_project_func": self.is_project_func(),
            "indent": self.indent(),
            "func_key": self._func_key(),
            "func_std_string": self.func_std_string(),
            "cumtime": self.cumtime(),
            "cumtime_per_call": self.cumtime_per_call(),
            "tottime": self.tottime(),
            "tottime_per_call": self.tottime_per_call(),
            "count": self.count(),
            "primitive_count": self.primitive_count(),
        }


def _print_stats_from_function_calls(func_list: list[FunctionCall]) -> str:
    """
    Create a string that is matches what pstats.Stats.print_stats would
    print out.
    """
    # Column layout matches pstats output: ncalls right-justified in 9
    # chars, each time value formatted as f8 ("%8.3f"). The 3-space indent
    # on the header and ordering lines is part of the pstats format.
    # https://docs.python.org/3/library/profile.html#pstats.Stats.print_stats
    lines = ["   Ordered by: cumulative time", ""]
    lines.append(
        "   ncalls  tottime  percall  cumtime  percall filename:lineno(function)"
    )
    for func in func_list:
        nc = func["count"]
        cc = func["primitive_count"]
        # pstats shows nc/cc when they differ (recursive calls inflate nc)
        ncalls_str = f"{nc}/{cc}" if nc != cc else str(nc)
        # pstats prints 8 spaces instead of a percall value when the
        # divisor is zero, preserving column alignment
        tt_per = f"{func['tottime_per_call']:8.3f}" if nc else " " * 8
        ct_per = f"{func['cumtime_per_call']:8.3f}" if cc else " " * 8
        lines.append(
            f"{ncalls_str:>9} {func['tottime']:8.3f} {tt_per}"
            f" {func['cumtime']:8.3f} {ct_per} {func['func_key']}"
        )
    # pstats ends output with two blank lines
    lines.extend(["", ""])
    return "\n".join(lines)


class ProfilingPanel(Panel):
    """
    Panel that displays profiling information.
    """

    is_async = False
    title = _("Profiling")

    template = "debug_toolbar/panels/profiling.html"
    capture_project_code = dt_settings.get_config()["PROFILER_CAPTURE_PROJECT_CODE"]

    def process_request(self, request):
        self.profiler = cProfile.Profile()
        return self.profiler.runcall(super().process_request, request)

    def add_node(self, func_list, func, max_depth, cum_time):
        func_list.append(func)
        if func.depth < max_depth:
            for subfunc in func.subfuncs():
                # Always include the user's code
                if subfunc.stats[3] >= cum_time or (
                    self.capture_project_code
                    and subfunc.is_project_func()
                    and subfunc.stats[3] > 0
                ):
                    func.has_subfuncs = True
                    self.add_node(func_list, subfunc, max_depth, cum_time)

    def generate_stats(self, request, response):
        if not hasattr(self, "profiler"):
            return None
        # Could be delayed until the panel content is requested (perf. optim.)
        self.profiler.create_stats()
        self.stats = Stats(self.profiler)
        self.stats.calc_callees()

        root_func = cProfile.label(super().process_request.__code__)
        if root_func in self.stats.stats:
            root = FunctionCall(self.stats, root_func, depth=0)
            func_list = []
            cum_time_threshold = (
                root.stats[3] / dt_settings.get_config()["PROFILER_THRESHOLD_RATIO"]
            )
            self.add_node(
                func_list,
                root,
                dt_settings.get_config()["PROFILER_MAX_DEPTH"],
                cum_time_threshold,
            )
            try:
                url_name = get_view_path_metadata(request).url_name
            except Http404:
                url_name = _("<unavailable>")
            self.record_stats(
                {
                    "func_list": [func.serialize() for func in func_list],
                    "profile_name": f"{url_name}-{timezone.now().isoformat()}",
                }
            )

    def get_stats(self):
        """
        Access data stored by the panel. Returns a :class:`dict`.
        """
        stats = super().get_stats()
        # This isn't a stat, but is used in the context in the
        # ProfilingPanel.content property when rendering the template.
        stats["profiling_download_form"] = ProfilingDownloadForm(
            initial={"request_id": self.toolbar.request_id}
        )
        return stats

    @classmethod
    def get_urls(cls):
        return [
            path("profiling_download/", profiling_download, name="profiling_download")
        ]


class ProfilingDownloadForm(forms.Form):
    """
    Validate params

        request_id: The key for the store instance to be fetched.
    """

    request_id = forms.CharField(widget=forms.HiddenInput())


@require_GET
@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def profiling_download(request):
    form = ProfilingDownloadForm(request.GET)

    if form.is_valid():
        request_id: str = form.cleaned_data["request_id"]
        toolbar: DebugToolbar | None = DebugToolbar.fetch(request_id)
        if toolbar is None:
            return HttpResponseBadRequest("Request is no longer available.")
        panel = toolbar.get_panel_by_id(ProfilingPanel.panel_id)
        panel_stats = panel.get_stats()
        if "func_list" not in panel_stats:
            return HttpResponseBadRequest("No profiling data exists for this request.")
        content = _print_stats_from_function_calls(panel_stats["func_list"])
        response = HttpResponse(content, content_type="text/plain")
        profile_name = panel_stats.get("profile_name") or f"request-{request_id}"
        response["Content-Disposition"] = f'attachment; filename="{profile_name}.prof"'
        return response
    return HttpResponseBadRequest(f"Form errors: {form.errors}")
