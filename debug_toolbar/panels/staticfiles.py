import contextlib
import uuid
from contextvars import ContextVar
from os.path import join, normpath

from django.contrib.staticfiles import finders, storage
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar import panels

# This will record and map the StaticFile instances with its associated
# request across threads and async concurrent requests state.
request_id_context_var = ContextVar("djdt_request_id_store")
record_static_file_signal = Signal()


class URLMixin:
    def url(self, path, *args, **kwargs):
        url = super().url(path, *args, **kwargs)
        with contextlib.suppress(LookupError):
            # For LookupError:
            # The ContextVar wasn't set yet. Since the toolbar wasn't properly
            # configured to handle this request, we don't need to capture
            # the static file.
            request_id = request_id_context_var.get()
            record_static_file_signal.send(
                sender=self,
                staticfile=(str(path), url, finders.find(str(path))),
                request_id=request_id,
            )
        return url


class StaticFilesPanel(panels.Panel):
    """
    A panel to display the found staticfiles.
    """

    is_async = True
    name = "Static files"
    template = "debug_toolbar/panels/staticfiles.html"

    @property
    def title(self):
        stats = self.get_stats()
        return _("Static files (%(num_found)s found, %(num_used)s used)") % {
            "num_found": stats.get("num_found"),
            "num_used": stats.get("num_used"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_found = 0
        self.used_paths = set()
        self.request_id = str(uuid.uuid4())

    @classmethod
    def ready(cls):
        cls = storage.staticfiles_storage.__class__
        if URLMixin not in cls.mro():
            cls.__bases__ = (URLMixin, *cls.__bases__)

    def _store_static_files_signal_handler(self, sender, staticfile, **kwargs):
        # Only record the static file if the request_id matches the one
        # that was used to create the panel.
        # as sender of the signal and this handler will have multiple
        # concurrent connections and we want to avoid storing of same
        # staticfile from other connections as well.
        if request_id_context_var.get() == self.request_id:
            self.used_paths.add(staticfile)

    def enable_instrumentation(self):
        self.ctx_token = request_id_context_var.set(self.request_id)
        record_static_file_signal.connect(self._store_static_files_signal_handler)

    def disable_instrumentation(self):
        record_static_file_signal.disconnect(self._store_static_files_signal_handler)
        request_id_context_var.reset(self.ctx_token)

    nav_title = _("Static files")

    @property
    def nav_subtitle(self):
        num_used = self.get_stats().get("num_used")
        return ngettext(
            "%(num_used)s file used", "%(num_used)s files used", num_used
        ) % {"num_used": num_used}

    def generate_stats(self, request, response):
        self.record_stats(
            {
                "num_found": self.num_found,
                "num_used": len(self.used_paths),
                "staticfiles": sorted(self.used_paths),
                "staticfiles_apps": self.get_staticfiles_apps(),
                "staticfiles_dirs": self.get_staticfiles_dirs(),
                "staticfiles_finders": self.get_staticfiles_finders(),
            }
        )

    def get_staticfiles_finders(self):
        """
        Returns a sorted mapping between the finder path and the list
        of relative and file system paths which that finder was able
        to find.
        """
        finders_mapping = {}
        for finder in finders.get_finders():
            try:
                for path, finder_storage in finder.list([]):
                    if getattr(finder_storage, "prefix", None):
                        prefixed_path = join(finder_storage.prefix, path)
                    else:
                        prefixed_path = path
                    finder_cls = finder.__class__
                    finder_path = ".".join([finder_cls.__module__, finder_cls.__name__])
                    real_path = finder_storage.path(path)
                    payload = (prefixed_path, real_path)
                    finders_mapping.setdefault(finder_path, []).append(payload)
                    self.num_found += 1
            except OSError:
                # This error should be captured and presented as a part of run_checks.
                pass
        return finders_mapping

    def get_staticfiles_dirs(self):
        """
        Returns a list of paths to inspect for additional static files
        """
        dirs = []
        for finder in finders.get_finders():
            if isinstance(finder, finders.FileSystemFinder):
                dirs.extend(finder.locations)
        return [(prefix, normpath(dir)) for prefix, dir in dirs]

    def get_staticfiles_apps(self):
        """
        Returns a list of app paths that have a static directory
        """
        apps = []
        for finder in finders.get_finders():
            if isinstance(finder, finders.AppDirectoriesFinder):
                for app in finder.apps:
                    if app not in apps:
                        apps.append(app)
        return apps
