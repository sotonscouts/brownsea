from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.paginator import Paginator
from django.db import models
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.models import Page
from wagtail.search import index


class BasePage(Page):
    show_in_menus_default = True

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
        paginator = context["sub_pages"] = Paginator(child_pages, per_page=10)

        return {
            **context,
            "sub_pages": paginator.get_page(page_number),
        }

    class Meta:
        abstract = True
