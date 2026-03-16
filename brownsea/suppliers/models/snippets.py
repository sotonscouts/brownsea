from django.db import models
from django.db.models import Case, FloatField, GeneratedField, When
from django.db.models.functions import Cast, Coalesce
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index

__all__ = ["SupplierCategory", "Supplier", "SupplierReview"]


class SupplierCategory(index.Indexed, models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional icon name or emoji",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("icon"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("description"),
    ]

    class Meta:
        verbose_name = "Supplier Category"
        verbose_name_plural = "Supplier Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(index.Indexed, models.Model):
    # Recommendation status choices
    RECOMMENDATION_PREFERRED = "preferred"
    RECOMMENDATION_APPROVED = "approved"
    RECOMMENDATION_LISTED = "listed"
    RECOMMENDATION_NOT_RECOMMENDED = "not_recommended"

    RECOMMENDATION_CHOICES = [
        (RECOMMENDATION_PREFERRED, "Preferred Supplier"),
        (RECOMMENDATION_APPROVED, "Approved Supplier"),
        (RECOMMENDATION_LISTED, "Listed (No Official Recommendation)"),
        (RECOMMENDATION_NOT_RECOMMENDED, "Not Recommended"),
    ]

    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        "SupplierCategory",
        on_delete=models.PROTECT,
        related_name="suppliers",
    )

    # Official Recommendation (organisational decision)
    recommendation_status = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
        default=RECOMMENDATION_LISTED,
        help_text="Official district recommendation status",
        db_index=True,
    )
    recommendation_notes = models.TextField(
        blank=True,
        help_text="Why this supplier has this status (internal notes)",
    )
    approved_by = models.ForeignKey(
        "core.Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_suppliers",
        help_text="Who approved/set this recommendation",
    )
    approval_date = models.DateField(null=True, blank=True)
    review_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this recommendation should be reviewed",
    )

    # Contact Details
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    primary_contact_name = models.CharField(max_length=255, blank=True)

    # Description & Services
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    description = models.TextField(help_text="Brief overview of what this supplier provides and why they're listed")
    services = RichTextField(blank=True, help_text="Detailed services/products offered")
    special_terms = models.TextField(
        blank=True,
        help_text="Any special discounts or terms for scouts members",
    )

    # Trust & Safety
    has_public_liability_insurance = models.BooleanField(default=False)
    insurance_details = models.TextField(blank=True)
    certifications = models.TextField(
        blank=True,
        help_text="Relevant certifications, accreditations, etc.",
    )

    # Metadata
    date_added = models.DateField(auto_now_add=True, help_text="When this supplier was added to the system")
    last_updated = models.DateField(auto_now=True, help_text="Last time any field was updated")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("slug"),
                FieldPanel("category"),
                FieldPanel("logo"),
            ],
            heading="Basic Information",
        ),
        MultiFieldPanel(
            [
                FieldPanel("recommendation_status"),
                FieldPanel("recommendation_notes"),
                FieldPanel("approved_by"),
                FieldPanel("approval_date"),
                FieldPanel("review_due_date"),
            ],
            heading="Official Recommendation",
        ),
        MultiFieldPanel(
            [
                FieldPanel("description"),
                FieldPanel("services"),
                FieldPanel("special_terms"),
            ],
            heading="Services & Description",
        ),
        MultiFieldPanel(
            [
                FieldPanel("website"),
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("primary_contact_name"),
                FieldPanel("address"),
            ],
            heading="Contact Details",
        ),
        MultiFieldPanel(
            [
                FieldPanel("has_public_liability_insurance"),
                FieldPanel("insurance_details"),
                FieldPanel("certifications"),
            ],
            heading="Trust & Safety",
        ),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("description"),
        index.SearchField("services"),
        index.SearchField("special_terms"),
        index.AutocompleteField("name"),
    ]

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierReview(index.Indexed, models.Model):
    # Rating choices
    RATING_CHOICES = [
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Good"),
        (5, "5 - Excellent"),
    ]

    supplier = models.ForeignKey(
        "Supplier",
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    # Attribution
    reviewing_group = models.CharField(
        max_length=255,
        help_text="e.g. '1st Southampton Scout Group', 'Southampton City District'",
    )
    reviewer_name = models.CharField(
        max_length=255,
        help_text="Person who submitted this review",
    )
    reviewer_email = models.EmailField(
        blank=True,
        help_text="For follow-up questions (not displayed publicly)",
    )
    review_date = models.DateField()

    # What they experienced
    service_used = models.CharField(
        max_length=255,
        help_text="What did you order/use from this supplier?",
    )
    order_date = models.DateField(
        null=True,
        blank=True,
        help_text="Approximately when did you use this supplier?",
    )

    # Their experience
    experience_summary = models.TextField(help_text="Overall summary of your experience")
    what_went_well = models.TextField(
        blank=True,
        verbose_name="What went well",
        help_text="Positive aspects",
    )
    what_could_improve = models.TextField(
        blank=True,
        verbose_name="What could be improved",
        help_text="Areas for improvement or concerns",
    )

    # Ratings
    would_use_again = models.BooleanField(
        null=True,
        blank=True,
        help_text="Would your group use this supplier again? Leave blank if unsure",
    )
    value_for_money = models.IntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
    )
    quality_rating = models.IntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
    )
    service_rating = models.IntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
    )

    # Generated field for average rating (only averages non-null ratings)
    average_rating = GeneratedField(
        expression=(
            Cast(
                Coalesce("value_for_money", 0) + Coalesce("quality_rating", 0) + Coalesce("service_rating", 0),
                FloatField(),
            )
            / (
                Case(
                    When(value_for_money__isnull=False, then=1.0),
                    default=0.0,
                )
                + Case(
                    When(quality_rating__isnull=False, then=1.0),
                    default=0.0,
                )
                + Case(
                    When(service_rating__isnull=False, then=1.0),
                    default=0.0,
                )
            )
        ),
        output_field=FloatField(),
        db_persist=True,
    )

    # Practical details
    delivery_time_actual = models.CharField(
        max_length=100,
        blank=True,
        help_text="How long did delivery/completion actually take?",
    )
    delivery_time_promised = models.CharField(
        max_length=100,
        blank=True,
        help_text="What was promised?",
    )

    # Admin & Display
    approved_for_display = models.BooleanField(
        default=False,
        help_text="Admin approval required before showing publicly",
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not displayed publicly)",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("supplier"),
                FieldPanel("reviewing_group"),
                FieldPanel("reviewer_name"),
                FieldPanel("reviewer_email"),
                FieldPanel("review_date"),
            ],
            heading="Review Details",
        ),
        MultiFieldPanel(
            [
                FieldPanel("service_used"),
                FieldPanel("order_date"),
                FieldPanel("experience_summary"),
                FieldPanel("what_went_well"),
                FieldPanel("what_could_improve"),
            ],
            heading="Experience",
        ),
        MultiFieldPanel(
            [
                FieldPanel("would_use_again"),
                FieldPanel("value_for_money"),
                FieldPanel("quality_rating"),
                FieldPanel("service_rating"),
            ],
            heading="Ratings",
        ),
        MultiFieldPanel(
            [
                FieldPanel("delivery_time_promised"),
                FieldPanel("delivery_time_actual"),
            ],
            heading="Delivery",
        ),
        MultiFieldPanel(
            [
                FieldPanel("approved_for_display"),
                FieldPanel("admin_notes"),
            ],
            heading="Administration",
        ),
    ]

    search_fields = [
        index.SearchField("experience_summary"),
        index.SearchField("what_went_well"),
        index.SearchField("what_could_improve"),
        index.SearchField("reviewing_group"),
        index.SearchField("service_used"),
    ]

    class Meta:
        verbose_name = "Supplier Review"
        verbose_name_plural = "Supplier Reviews"
        ordering = ["-review_date"]

    def __str__(self):
        return f"{self.supplier.name} - {self.reviewing_group} ({self.review_date})"
