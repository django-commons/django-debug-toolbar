import contextlib
import uuid
from contextvars import ContextVar
from os.path import join, normpath

from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.dispatch import Signal
from django.utils.functional import LazyObject
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar import panels


class StaticFile:
    """
    Representing the different properties of a static file.
    """

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

    def real_path(self):
        return finders.find(self.path)

    def url(self):
        return storage.staticfiles_storage.url(self.path)


# This will record and map the StaticFile instances with its associated
# request across threads and async concurrent requests state.
request_id_context_var = ContextVar("djdt_request_id_store")
record_static_file_signal = Signal()


class DebugConfiguredStorage(LazyObject):
    """
    A staticfiles storage class to be used for collecting which paths
    are resolved by using the {% static %} template tag (which uses the
    `url` method).
    """

    def _setup(self):
        try:
            # From Django 4.2 use django.core.files.storage.storages in favor
            # of the deprecated django.core.files.storage.get_storage_class
            from django.core.files.storage import storages

            configured_storage_cls = storages["staticfiles"].__class__
        except ImportError:
            # Backwards compatibility for Django versions prior to 4.2
            from django.core.files.storage import get_storage_class

            configured_storage_cls = get_storage_class(settings.STATICFILES_STORAGE)

        class DebugStaticFilesStorage(configured_storage_cls):
            def url(self, path):
                with contextlib.suppress(LookupError):
                    # For LookupError:
                    # The ContextVar wasn't set yet. Since the toolbar wasn't properly
                    # configured to handle this request, we don't need to capture
                    # the static file.
                    request_id = request_id_context_var.get()
                    record_static_file_signal.send(
                        sender=self,
                        staticfile=StaticFile(path),
                        request_id=request_id,
                    )
                return super().url(path)

        self._wrapped = DebugStaticFilesStorage()


_original_storage = storage.staticfiles_storage


class StaticFilesPanel(panels.Panel):
    """
    A panel to display the found staticfiles.
    """

    is_async = True
    name = "Static files"
    template = "debug_toolbar/panels/staticfiles.html"

    @property
    def title(self):
        return _("Static files (%(num_found)s found, %(num_used)s used)") % {
            "num_found": self.num_found,
            "num_used": self.num_used,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_found = 0
        self.used_paths = []
        self.request_id = str(uuid.uuid4())

    @classmethod
    def ready(cls):
        storage.staticfiles_storage = DebugConfiguredStorage()

    def _store_static_files_signal_handler(self, sender, staticfile, **kwargs):
        # Only record the static file if the request_id matches the one
        # that was used to create the panel.
        # as sender of the signal and this handler will have multiple
        # concurrent connections and we want to avoid storing of same
        # staticfile from other connections as well.
        if request_id_context_var.get() == self.request_id:
            self.used_paths.append(staticfile)

    def enable_instrumentation(self):
        record_static_file_signal.connect(self._store_static_files_signal_handler)
        self.ctx_token = request_id_context_var.set(self.request_id)

    def disable_instrumentation(self):
        record_static_file_signal.disconnect(self._store_static_files_signal_handler)
        request_id_context_var.reset(self.ctx_token)

    @property
    def num_used(self):
        stats = self.get_stats()
        return stats and stats["num_used"]

    nav_title = _("Static files")

    @property
    def nav_subtitle(self):
        num_used = self.num_used
        return ngettext(
            "%(num_used)s file used", "%(num_used)s files used", num_used
        ) % {"num_used": num_used}

    def generate_stats(self, request, response):
        self.record_stats(
            {
                "num_found": self.num_found,
                "num_used": len(self.used_paths),
                "staticfiles": self.used_paths,
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
