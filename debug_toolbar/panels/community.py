from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel


class CommunityPanel(Panel):
    """
    A panel that provides links to the Django Debug Toolbar community.
    """

    is_async = True

    title = _("Community")
    template = "debug_toolbar/panels/community.html"

    def process_request(self, request):
        self.record_stats({"community": "community"})
        return super().process_request(request)
