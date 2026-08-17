from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import Panel


class MagicLinksPanel(Panel):
    def __init__(self, **kwargs):
        kwargs.setdefault("heading", _("Magic links"))
        super().__init__(**kwargs)

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/magic_links_panel.html"

        def is_shown(self):
            from brownsea.core.models import PageAccessLevel

            if not self.instance.pk:
                return False

            specific_page = self.instance.specific
            if not hasattr(specific_page, "get_effective_access_level"):
                return False

            return specific_page.get_effective_access_level() == PageAccessLevel.MAGIC_LINK

        def get_context_data(self, parent_context=None):
            from brownsea.core.magic_links import build_magic_link_url
            from brownsea.core.models import PageMagicLink

            context = super().get_context_data(parent_context)
            page = self.instance
            magic_links = PageMagicLink.objects.filter(page=page)
            active_links = list(magic_links.active())
            inactive_links = [link for link in magic_links if not link.is_active]

            context.update(
                {
                    "page": page,
                    "active_links": [
                        {
                            "link": link,
                            "share_url": build_magic_link_url(link, self.request),
                        }
                        for link in active_links
                    ],
                    "inactive_links": inactive_links,
                    "create_url": reverse("core:magic_links_create", args=[page.id]),
                }
            )
            return context
