from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.search import index

from brownsea.core.models import BasePage
from brownsea.suppliers.models.snippets import Supplier, SupplierCategory

__all__ = ["SupplierListPage"]


class SupplierListPage(RoutablePageMixin, BasePage):
    template = "pages/suppliers/supplier_list_page.html"
    max_count = 1  # Only one supplier list page
    subpage_types = []

    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel("All suppliers will be listed here."),
    ]
    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    def get_suppliers(self):
        """Get all suppliers with their review statistics

        Note: positive_review_count and negative_review_count may not sum to review_count
        because some reviews may have would_use_again=null (reviewer was unsure).
        """
        from django.db.models import Max

        return (
            Supplier.objects.select_related("category", "approved_by")
            .prefetch_related("reviews")
            .annotate(
                avg_rating=Avg("reviews__average_rating", filter=Q(reviews__approved_for_display=True)),
                review_count=Count("reviews", filter=Q(reviews__approved_for_display=True)),
                positive_review_count=Count(
                    "reviews",
                    filter=Q(reviews__approved_for_display=True, reviews__would_use_again=True),
                ),
                negative_review_count=Count(
                    "reviews",
                    filter=Q(reviews__approved_for_display=True, reviews__would_use_again=False),
                ),
                last_review_date=Max("reviews__review_date", filter=Q(reviews__approved_for_display=True)),
            )
            .order_by("name")
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        suppliers = self.get_suppliers()

        # Get all categories for filtering UI
        categories = SupplierCategory.objects.all()

        # Search suppliers using Wagtail's search framework
        search_query = request.GET.get("search", "").strip()
        if search_query:
            suppliers = suppliers.search(search_query)

        # Filter by category if specified
        category_slug = request.GET.get("category")
        selected_category = None
        if category_slug:
            selected_category = get_object_or_404(SupplierCategory, slug=category_slug)
            suppliers = suppliers.filter(category=selected_category)

        # Filter by recommendation status if specified
        recommendation = request.GET.get("recommendation")
        if recommendation:
            suppliers = suppliers.filter(recommendation_status=recommendation)

        # Pagination
        page_number = request.GET.get("page")
        paginator = Paginator(suppliers, per_page=settings.APP_SEARCH_RESULTS_PER_PAGE)

        context.update(
            {
                "suppliers_page": paginator.get_page(page_number),
                "categories": categories,
                "selected_category": selected_category,
                "selected_recommendation": recommendation,
                "search_query": search_query,
                "recommendation_choices": Supplier.RECOMMENDATION_CHOICES,
            }
        )

        return context

    @route(r"^category/([^/]+)/$")
    def category_view(self, request, category_slug):
        """Filter suppliers by category"""
        category = get_object_or_404(SupplierCategory, slug=category_slug)

        suppliers = self.get_suppliers().filter(category=category)

        # Pagination
        page_number = request.GET.get("page")
        paginator = Paginator(suppliers, per_page=settings.APP_SEARCH_RESULTS_PER_PAGE)

        context = self.get_context(request)
        context.update(
            {
                "suppliers_page": paginator.get_page(page_number),
                "selected_category": category,
            }
        )

        return self.render(request, context_overrides=context)

    @route(r"^supplier/([^/]+)/$")
    def supplier_detail(self, request, supplier_slug):
        """Individual supplier detail view"""
        supplier = get_object_or_404(
            Supplier.objects.select_related("category", "approved_by").prefetch_related("reviews"),
            slug=supplier_slug,
        )

        # Get approved reviews
        reviews = supplier.reviews.filter(approved_for_display=True).order_by("-review_date")

        # Separate positive and negative reviews
        positive_reviews = reviews.filter(would_use_again=True)
        negative_reviews = reviews.filter(would_use_again=False)

        # Calculate statistics
        if reviews.exists():
            avg_value = reviews.aggregate(avg=Avg("value_for_money"))["avg"]
            avg_quality = reviews.aggregate(avg=Avg("quality_rating"))["avg"]
            avg_service = reviews.aggregate(avg=Avg("service_rating"))["avg"]
            avg_overall = reviews.aggregate(avg=Avg("average_rating"))["avg"]
        else:
            avg_value = avg_quality = avg_service = avg_overall = None

        context = self.get_context(request)
        context.update(
            {
                "supplier": supplier,
                "reviews": reviews,
                "positive_reviews": positive_reviews,
                "negative_reviews": negative_reviews,
                "review_stats": {
                    "count": reviews.count(),
                    "avg_value": avg_value,
                    "avg_quality": avg_quality,
                    "avg_service": avg_service,
                    "avg_overall": avg_overall,
                    "positive_count": positive_reviews.count(),
                    "negative_count": negative_reviews.count(),
                },
            }
        )

        return self.render(request, template="pages/suppliers/supplier_detail.html", context_overrides=context)
