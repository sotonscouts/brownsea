from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.forms import ValidationError
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.models import Page, PreviewableMixin
from wagtail.search import index


class BasePage(Page):
    show_in_menus_default = True

    promote_panels = Page.promote_panels
    settings_panels = Page.settings_panels

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

    def serve_preview(self, request, mode_name):
        template = self.get_preview_template(request, mode_name)
        context = {
            "value": self,
            "request": request,
            "is_preview": True,
            "template_name": template,
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
