from debug_toolbar.panels import Panel
from django.utils.translation import gettext_lazy as _

class CommunityPanel(Panel):
    """
    A panel that provides links to the Django Debug Toolbar community.
    """

    title = _("Community")
    template = "debug_toolbar/panels/community.html"

    def nav_title(self):
        return _("Community")
