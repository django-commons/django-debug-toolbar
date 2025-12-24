import contextlib
import json
from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils.module_loading import import_string

from debug_toolbar import settings as dt_settings
from debug_toolbar.models import HistoryEntry
from debug_toolbar.sanitize import force_str


class DebugToolbarJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except (TypeError, ValueError):
            return force_str(o)


def serialize(data: Any) -> str:
    # If this starts throwing an exceptions, consider
    # Subclassing DjangoJSONEncoder and using force_str to
    # make it JSON serializable.
    return json.dumps(data, cls=DebugToolbarJSONEncoder)


def deserialize(data: str) -> Any:
    return json.loads(data)


class BaseStore:
    @classmethod
    def request_ids(cls) -> Iterable:
        """The stored request ids"""
        raise NotImplementedError

    @classmethod
    def exists(cls, request_id: str) -> bool:
        """Does the given request_id exist in the store"""
        raise NotImplementedError

    @classmethod
    def set(cls, request_id: str):
        """Set a request_id in the store"""
        raise NotImplementedError

    @classmethod
    def clear(cls):
        """Remove all requests from the request store"""
        raise NotImplementedError

    @classmethod
    def delete(cls, request_id: str):
        """Delete the store for the given request_id"""
        raise NotImplementedError

    @classmethod
    def save_panel(cls, request_id: str, panel_id: str, data: Any = None):
        """Save the panel data for the given request_id"""
        raise NotImplementedError

    @classmethod
    def panel(cls, request_id: str, panel_id: str) -> Any:
        """Fetch the panel data for the given request_id"""
        raise NotImplementedError


class MemoryStore(BaseStore):
    # ids is the collection of storage ids that have been used.
    # Use a dequeue to support O(1) appends and pops
    # from either direction.
    _request_ids: deque = deque()
    _request_store: dict[str, dict] = defaultdict(dict)

    @classmethod
    def request_ids(cls) -> Iterable:
        """The stored request ids"""
        return cls._request_ids

    @classmethod
    def exists(cls, request_id: str) -> bool:
        """Does the given request_id exist in the request store"""
        return request_id in cls._request_ids

    @classmethod
    def set(cls, request_id: str):
        """Set a request_id in the request store"""
        if request_id not in cls._request_ids:
            cls._request_ids.append(request_id)
        for _ in range(
            len(cls._request_ids) - dt_settings.get_config()["RESULTS_CACHE_SIZE"]
        ):
            removed_id = cls._request_ids.popleft()
            cls._request_store.pop(removed_id, None)

    @classmethod
    def clear(cls):
        """Remove all requests from the request store"""
        cls._request_ids.clear()
        cls._request_store.clear()

    @classmethod
    def delete(cls, request_id: str):
        """Delete the stored request for the given request_id"""
        cls._request_store.pop(request_id, None)
        # Suppress when request_id doesn't exist in the collection of ids.
        with contextlib.suppress(ValueError):
            cls._request_ids.remove(request_id)

    @classmethod
    def save_panel(cls, request_id: str, panel_id: str, data: Any = None):
        """Save the panel data for the given request_id"""
        cls.set(request_id)
        cls._request_store[request_id][panel_id] = serialize(data)

    @classmethod
    def panel(cls, request_id: str, panel_id: str) -> Any:
        """Fetch the panel data for the given request_id"""
        try:
            data = cls._request_store[request_id][panel_id]
        except KeyError:
            return {}
        else:
            return deserialize(data)

    @classmethod
    def panels(cls, request_id: str) -> Any:
        """Fetch all the panel data for the given request_id"""
        try:
            panel_mapping = cls._request_store[request_id]
        except KeyError:
            return {}
        for panel, data in panel_mapping.items():
            yield panel, deserialize(data)


class DatabaseStore(BaseStore):
    @classmethod
    def _cleanup_old_entries(cls):
        """
        Enforce the cache size limit - keeping only the most recently used entries
        up to RESULTS_CACHE_SIZE.
        """
        # Determine which entries to keep
        keep_ids = cls.request_ids()

        # Delete all entries not in the keep list
        if keep_ids:
            HistoryEntry.objects.exclude(request_id__in=keep_ids).delete()

    @classmethod
    def request_ids(cls):
        """Return all stored request ids within the cache size limit"""
        cache_size = dt_settings.get_config()["RESULTS_CACHE_SIZE"]
        return list(
            HistoryEntry.objects.all()[:cache_size].values_list("request_id", flat=True)
        )

    @classmethod
    def exists(cls, request_id: str) -> bool:
        """Check if the given request_id exists in the store"""
        return HistoryEntry.objects.filter(request_id=request_id).exists()

    @classmethod
    def set(cls, request_id: str):
        """Set a request_id in the store and clean up old entries"""
        with transaction.atomic():
            # Create the entry if it doesn't exist (ignore otherwise)
            _, created = HistoryEntry.objects.get_or_create(request_id=request_id)

            # Only enforce cache size limit when new entries are created
            if created:
                cls._cleanup_old_entries()

    @classmethod
    def clear(cls):
        """Remove all requests from the store"""
        HistoryEntry.objects.all().delete()

    @classmethod
    def delete(cls, request_id: str):
        """Delete the stored request for the given request_id"""
        HistoryEntry.objects.filter(request_id=request_id).delete()

    @classmethod
    def save_panel(cls, request_id: str, panel_id: str, data: Any = None):
        """Save the panel data for the given request_id"""
        with transaction.atomic():
            obj, _ = HistoryEntry.objects.get_or_create(request_id=request_id)
            store_data = obj.data
            store_data[panel_id] = serialize(data)
            obj.data = store_data
            obj.save()

    @classmethod
    def panel(cls, request_id: str, panel_id: str) -> Any:
        """Fetch the panel data for the given request_id"""
        try:
            data = HistoryEntry.objects.get(request_id=request_id).data
            panel_data = data.get(panel_id)
            if panel_data is None:
                return {}
            return deserialize(panel_data)
        except HistoryEntry.DoesNotExist:
            return {}

    @classmethod
    def panels(cls, request_id: str) -> Any:
        """Fetch all panel data for the given request_id"""
        try:
            data = HistoryEntry.objects.get(request_id=request_id).data
            for panel_id, panel_data in data.items():
                yield panel_id, deserialize(panel_data)
        except HistoryEntry.DoesNotExist:
            return {}


def get_store() -> BaseStore:
    return import_string(dt_settings.get_config()["TOOLBAR_STORE_CLASS"])
