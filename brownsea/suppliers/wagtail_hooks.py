from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Supplier, SupplierCategory, SupplierReview


class SupplierCategoryViewSet(SnippetViewSet):
    model = SupplierCategory
    menu_label = "Categories"
    list_display = ("name", "slug", "icon")
    search_fields = ("name",)
    icon = "tag"


class SupplierViewSet(SnippetViewSet):
    model = Supplier
    menu_label = "Suppliers"
    list_display = ("name", "category", "recommendation_status", "last_updated")
    list_filter = ("category", "recommendation_status", "has_public_liability_insurance")
    search_fields = ("name", "description", "services")
    list_export = ("name", "category", "recommendation_status", "website", "email", "phone")
    icon = "site"


class SupplierReviewViewSet(SnippetViewSet):
    model = SupplierReview
    menu_label = "Reviews"
    list_display = ("supplier", "reviewing_group", "review_date", "average_rating", "approved_for_display")
    list_filter = ("approved_for_display", "would_use_again", "supplier", "review_date")
    search_fields = ("supplier__name", "reviewing_group", "experience_summary")
    list_export = (
        "supplier",
        "reviewing_group",
        "review_date",
        "service_used",
        "average_rating",
        "would_use_again",
    )
    icon = "form"


@register_snippet
class SupplierViewSetGroup(SnippetViewSetGroup):
    menu_label = "Suppliers"
    menu_icon = "site"
    menu_order = 300
    items = (SupplierViewSet, SupplierCategoryViewSet, SupplierReviewViewSet)
