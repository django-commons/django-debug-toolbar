import cProfile
import os
from colorsys import hsv_to_rgb
from pstats import Stats

from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from debug_toolbar import settings as dt_settings
from debug_toolbar.panels import Panel


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

    def serialize(self):
        return {
            "has_subfuncs": self.has_subfuncs,
            "id": self.id,
            "parent_ids": self.parent_ids,
            "is_project_func": self.is_project_func(),
            "indent": self.indent(),
            "func_std_string": self.func_std_string(),
            "cumtime": self.cumtime(),
            "cumtime_per_call": self.cumtime_per_call(),
            "tottime": self.tottime(),
            "tottime_per_call": self.tottime_per_call(),
            "count": self.count(),
        }


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
            self.record_stats({"func_list": [func.serialize() for func in func_list]})
