import uuid

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import models
from django.forms import ValidationError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Page, PreviewableMixin
from wagtail.search import index

from brownsea.core.blocks import HeadingBlock
from brownsea.core.panels import MagicLinksPanel
from brownsea.core.themes import THEMES, get_theme


class PageAccessLevel(models.TextChoices):
    INHERIT = "inherit", _("Inherit")
    LOGGED_IN = "logged_in", _("Logged in only")
    MAGIC_LINK = "magic_link", _("Magic link")
    PUBLIC = "public", _("Public")


class PageMagicLinkQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(revoked_at__isnull=True).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )


class PageMagicLink(models.Model):
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="magic_links",
    )
    token_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    label = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    objects = PageMagicLinkQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.label or f"Magic link for {self.page.title}"

    @property
    def is_active(self):
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and timezone.now() >= self.expires_at:
            return False
        return True

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])


class BasePage(Page):
    show_in_menus_default = True

    access_level = models.CharField(
        max_length=20,
        choices=PageAccessLevel.choices,
        default=PageAccessLevel.INHERIT,
    )

    promote_panels = Page.promote_panels
    settings_panels = Page.settings_panels
    security_panels = [
        MultiFieldPanel(
            [
                FieldPanel("access_level"),
            ],
            heading=_("Page access"),
            help_text=_(
                "Child pages set to Inherit will use the nearest ancestor's setting. "
                "Pages above the site home default to logged in only. "
                "Magic link pages can also be shared from the section below or the Share button on the site."
            ),
        ),
        MagicLinksPanel(),
    ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        meta = cls.__dict__.get("Meta")
        if meta is not None and getattr(meta, "abstract", False):
            return
        if "edit_handler" in cls.__dict__:
            return

        tabs = []
        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels, heading=_("Content")))
        if cls.security_panels:
            tabs.append(ObjectList(cls.security_panels, heading=_("Security")))
        if cls.promote_panels:
            tabs.append(ObjectList(cls.promote_panels, heading=_("Promote")))
        if cls.settings_panels:
            tabs.append(ObjectList(cls.settings_panels, heading=_("Settings")))

        cls.edit_handler = TabbedInterface(tabs, base_form_class=getattr(cls, "base_form_class", None))

    def get_effective_access_level(self):
        for page in reversed(self.specific.get_ancestors(inclusive=True)):
            if page.is_root():
                continue
            specific_page = page.specific
            if specific_page.access_level != PageAccessLevel.INHERIT:
                return specific_page.access_level
        return PageAccessLevel.LOGGED_IN

    def allow_anonymous_access(self, request):
        effective_access = self.get_effective_access_level()
        if effective_access == PageAccessLevel.PUBLIC:
            return True
        if effective_access == PageAccessLevel.MAGIC_LINK:
            from brownsea.core.magic_links import has_magic_link_access

            return has_magic_link_access(request, self)
        return False

    def serve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            access_token = request.GET.get("access")
            if access_token:
                from brownsea.core.magic_links import redeem_magic_link_token

                if redeem_magic_link_token(request, access_token, self):
                    return redirect(self.get_url(request) or self.url)

            if not self.allow_anonymous_access(request):
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        return super().serve(request, *args, **kwargs)

    def serve_password_required_response(self, request, form, action_url):
        form.helper = FormHelper()
        form.helper.form_action = action_url
        form.helper.form_method = "post"
        form.helper.add_input(Submit("submit", "Continue"))

        return super().serve_password_required_response(request, form, action_url)

    class Meta:
        abstract = True


class AbstractIndexPage(BasePage):
    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel("All child pages will be listed."),
    ]
    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    def get_context(self, request):
        context = super().get_context(request)

        child_pages = self.get_children().live().filter(show_in_menus=True)

        page_number = request.GET.get("page")
        paginator = context["sub_pages"] = Paginator(
            child_pages,
            per_page=settings.APP_SEARCH_RESULTS_PER_PAGE,
        )

        return {
            **context,
            "sub_pages": paginator.get_page(page_number),
        }

    class Meta:
        abstract = True


class BrownseaPreviewableMixin(PreviewableMixin):
    """A custom PreviewableMixin that renders previews with proper styling."""

    preview_full_bleed = False

    def serve_preview(self, request, mode_name):
        template = self.get_preview_template(request, mode_name)
        context = {
            "value": self,
            "request": request,
            "is_preview": True,
            "template_name": template,
            "preview_full_bleed": self.preview_full_bleed,
        }
        return render(request, "components/preview_wrapper.html", context)

    preview_sizes = [
        {
            "name": "mobile",
            "icon": "mobile-alt",
            "device_width": 375,
            "label": "Preview in mobile size",
        },
        {
            "name": "tablet",
            "icon": "tablet-alt",
            "device_width": 768,
            "label": "Preview in tablet size",
        },
    ]


class Author(BrownseaPreviewableMixin, models.Model):
    """A reusable Author snippet."""

    name = models.CharField(max_length=255, help_text="The author's name")
    role = models.TextField(blank=True, help_text="The author's role or title")
    profile_picture = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="An optional profile picture for the author",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("role"),
        FieldPanel("profile_picture"),
    ]

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name

    def get_preview_template(self, request, mode_name):
        return "components/author_card.html"


class CallToAction(BrownseaPreviewableMixin, models.Model):
    """A reusable Call to Action snippet."""

    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    link_text = models.CharField(max_length=50, help_text="The text to display on the button, e.g. 'Find out more'")

    page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="An internal page to link to.",
    )
    external_url = models.URLField(blank=True, help_text="An external URL to link to.")

    panels = [
        FieldPanel("title"),
        FieldPanel("summary"),
        MultiFieldPanel(
            [
                FieldPanel("link_text"),
                FieldPanel("page"),
                FieldPanel("external_url"),
            ],
            heading="Link Details",
        ),
    ]

    class Meta:
        verbose_name = "Call to Action"
        verbose_name_plural = "Calls to Action"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.page and self.external_url:
            raise ValidationError("Please choose either an internal page OR an external URL, not both.")
        if not self.page and not self.external_url:
            raise ValidationError("Please choose either an internal page OR an external URL.")

    @property
    def url(self):
        return self.page.url if self.page else self.external_url

    def get_preview_template(self, request, mode_name):
        return "components/streamfield/blocks/call_to_action_block.html"


@register_setting(icon="cog")
class ThemeSettings(BrownseaPreviewableMixin, BaseSiteSetting):
    colour = models.CharField(
        max_length=20,
        choices=[(theme.slug, theme.label) for theme in THEMES.values()],
        default="white",
        help_text=_(
            "Scout brand colour for the navigation bar and primary buttons. "
            "White keeps a light navigation bar with purple buttons."
        ),
    )
    unit_name = models.CharField(
        max_length=255,
        default="Brownsea CMS",
        verbose_name=_("Unit name"),
        help_text=_("Shown under the Scout logo in the navigation bar. Not used if a custom logo is uploaded."),
    )
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Optional. Replaces the default Scout logo and unit name in the navigation bar."),
    )

    panels = [
        FieldPanel("unit_name"),
        FieldPanel("logo"),
        FieldPanel("colour"),
    ]

    preview_full_bleed = True
    preview_sizes = PreviewableMixin.DEFAULT_PREVIEW_SIZES

    @property
    def default_preview_size(self):
        return "desktop"

    @property
    def theme(self):
        return get_theme(self.colour)

    def get_preview_template(self, request, mode_name):
        return "components/theme_preview.html"

    def serve_preview(self, request, mode_name):
        request.preview_theme_settings = self
        return super().serve_preview(request, mode_name)


@register_setting(icon="warning")
class AlertBannerSettings(BaseSiteSetting):
    enabled = models.BooleanField(
        default=False,
        help_text="Enable or disable the alert banner across the site",
    )
    message = models.TextField(
        blank=True,
        help_text="The message to display in the alert banner",
    )
    type = models.CharField(
        max_length=20,
        choices=[
            ("info", "Information"),
            ("warning", "Warning"),
            ("danger", "Error"),
            ("success", "Success"),
        ],
        default="info",
        help_text="The type of alert to display",
    )
    button_text = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional text for the call-to-action button",
    )
    button_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optional internal page to link to",
    )
    button_external_url = models.URLField(
        blank=True,
        help_text="Optional external URL to link to",
    )

    panels = [
        FieldPanel("enabled"),
        FieldPanel("message"),
        FieldPanel("type"),
        MultiFieldPanel(
            [
                FieldPanel("button_text"),
                FieldPanel("button_page"),
                FieldPanel("button_external_url"),
            ],
            heading="Call to Action Button (Optional)",
        ),
    ]

    def clean(self):
        super().clean()
        if self.button_text:
            if self.button_page and self.button_external_url:
                raise ValidationError(
                    "Please choose either an internal page OR an external URL for the button, not both."
                )
            if not self.button_page and not self.button_external_url:
                raise ValidationError(
                    "If providing button text, please choose either an internal page OR an external URL."
                )
        elif self.button_page or self.button_external_url:
            raise ValidationError("Button text is required if specifying a button link.")

    @property
    def button_url(self):
        return self.button_page.url if self.button_page else self.button_external_url


class InPageNavMixin:
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        headings = []
        for block in self.body:
            if isinstance(block.block, HeadingBlock):
                headings.append(block.value["heading"])

        # If there are 3 or more heading blocks, add them to the context, so
        # that the in-page navigation is shown
        if len(headings) >= 3:
            context["in_page_nav"] = headings
        else:
            context["in_page_nav"] = None

        return context
