import weakref

from django.core.signals import (
    got_request_exception,
    request_finished,
    request_started,
    setting_changed,
)
from django.db.backends.signals import connection_created
from django.db.models.signals import (
    class_prepared,
    m2m_changed,
    post_delete,
    post_init,
    post_migrate,
    post_save,
    pre_delete,
    pre_init,
    pre_migrate,
    pre_save,
)
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar.panels import Panel


class SignalsPanel(Panel):
    template = "debug_toolbar/panels/signals.html"

    is_async = True

    SIGNALS = {
        "request_started": request_started,
        "request_finished": request_finished,
        "got_request_exception": got_request_exception,
        "connection_created": connection_created,
        "class_prepared": class_prepared,
        "pre_init": pre_init,
        "post_init": post_init,
        "pre_save": pre_save,
        "post_save": post_save,
        "pre_delete": pre_delete,
        "post_delete": post_delete,
        "m2m_changed": m2m_changed,
        "pre_migrate": pre_migrate,
        "post_migrate": post_migrate,
        "setting_changed": setting_changed,
    }

    def nav_subtitle(self):
        signals = self.get_stats()["signals"]
        num_receivers = sum(len(receivers) for name, receivers in signals)
        num_signals = len(signals)
        # here we have to handle a double count translation, hence the
        # hard coding of one signal
        if num_signals == 1:
            return ngettext(
                "%(num_receivers)d receiver of 1 signal",
                "%(num_receivers)d receivers of 1 signal",
                num_receivers,
            ) % {"num_receivers": num_receivers}
        return ngettext(
            "%(num_receivers)d receiver of %(num_signals)d signals",
            "%(num_receivers)d receivers of %(num_signals)d signals",
            num_receivers,
        ) % {"num_receivers": num_receivers, "num_signals": num_signals}

    title = _("Signals")
    nav_icon = "debug_toolbar/img/signals.svg"

    @property
    def signals(self):
        signals = self.SIGNALS.copy()
        for signal in self.toolbar.config["EXTRA_SIGNALS"]:
            signal_name = signal.rsplit(".", 1)[-1]
            signals[signal_name] = import_string(signal)
        return signals

    def generate_stats(self, request, response):
        signals = []
        for name, signal in sorted(self.signals.items()):
            receivers = []
            for receiver in signal.receivers:
                receiver = receiver[1]
                if isinstance(receiver, weakref.ReferenceType):
                    receiver = receiver()
                if receiver is None:
                    continue

                receiver = getattr(receiver, "__wraps__", receiver)
                receiver_name = getattr(receiver, "__name__", str(receiver))
                if getattr(receiver, "__self__", None) is not None:
                    receiver_class_name = getattr(
                        receiver.__self__, "__class__", type
                    ).__name__
                    text = f"{receiver_class_name}.{receiver_name}"
                else:
                    text = receiver_name
                receivers.append(text)
            signals.append((name, receivers))

        self.record_stats({"signals": signals})
