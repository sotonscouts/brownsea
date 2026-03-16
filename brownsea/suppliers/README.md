# Suppliers App

A Django/Wagtail application for managing supplier recommendations and reviews for scout groups.

## Features

### Supplier Management
- **Categorised suppliers** with custom categories (e.g., camping equipment, badges, insurance)
- **Recommendation levels**: Preferred, Approved, Listed, Not Recommended
- **Comprehensive supplier information**: contact details, services, special terms for scouts
- **Trust & Safety fields**: insurance details, certifications
- **Approval workflow**: track who approved suppliers and when reviews are due

### Review System
- **Group-based reviews**: reviews attributed to specific scout groups
- **Multiple rating dimensions**: value for money, quality, service
- **Smart average calculation**: only averages non-null ratings (e.g., if only quality is rated, average = quality rating, not quality/3)
- **Would use again** indicator (can be null if reviewer unsure)
- **Detailed feedback**: what went well, what could improve, delivery times
- **Moderation**: reviews require admin approval before display

### Public-Facing Pages
- **Filterable supplier list**: search by name, filter by category and recommendation status
- **Individual supplier pages**: full details with approved reviews separated into positive/negative
- **Clean URLs**: `/suppliers/`, `/suppliers/category/camping/`, `/suppliers/supplier/acme-badges/`
- **Review statistics**: average ratings, review counts, last review date

## Models

### SupplierCategory
Categories for organising suppliers (e.g., "Camping Equipment", "Uniform & Badges").

**Fields:**
- `name`: Category name
- `slug`: URL-friendly slug
- `description`: Optional description
- `icon`: Optional icon/emoji for display

### Supplier
Individual supplier records with full contact and service details.

**Key Fields:**
- `name`, `slug`: Basic identification
- `category`: ForeignKey to SupplierCategory
- `recommendation_status`: Official district recommendation (indexed for filtering)
- `recommendation_notes`: Why this status was assigned
- `approved_by`: ForeignKey to Author (who approved)
- `approval_date`, `review_due_date`: Approval workflow dates
- `website`, `email`, `phone`, `address`, `primary_contact_name`: Contact details
- `logo`: Optional supplier logo
- `description`: Brief overview (required)
- `services`: Rich text field for detailed services
- `special_terms`: Any discounts/terms for scouts
- `has_public_liability_insurance`, `insurance_details`, `certifications`: Trust & safety
- `date_added`, `last_updated`: Automatic timestamps

**Search Fields:**
- Name (full search + autocomplete)
- Description
- Services
- Special terms

### SupplierReview
Reviews from scout groups about their experiences with suppliers.

**Key Fields:**
- `supplier`: ForeignKey to Supplier
- `reviewing_group`: Name of the group (e.g., "1st Southampton Scout Group")
- `reviewer_name`, `reviewer_email`: Attribution (email not public)
- `review_date`: When review was submitted
- `service_used`: What they ordered/used
- `order_date`: Approximately when
- `experience_summary`: Overall summary (required)
- `what_went_well`, `what_could_improve`: Detailed feedback
- `would_use_again`: Boolean (nullable - can be unsure)
- `value_for_money`, `quality_rating`, `service_rating`: 1-5 star ratings (nullable)
- `average_rating`: Generated field - auto-calculated average of non-null ratings
- `delivery_time_promised`, `delivery_time_actual`: Practical details
- `approved_for_display`: Admin moderation flag
- `admin_notes`: Internal notes (not public)

**Average Rating Calculation:**
The `average_rating` is a database-generated field that intelligently averages only the ratings that were provided. For example:
- If all three ratings provided: `(value + quality + service) / 3`
- If only two provided: `(value + quality) / 2`
- If only one provided: that rating value

This ensures the average truly reflects the given ratings, not artificially lowered by missing data.

### SupplierListPage
Wagtail page type (singleton) that displays all suppliers with filtering and individual supplier views.

**URL Patterns:**
- `/suppliers/` - Main list with filters
- `/suppliers/category/<slug>/` - Filter by category
- `/suppliers/supplier/<slug>/` - Individual supplier detail

**Querystring Filters:**
- `?search=term` - Search supplier names, descriptions, services
- `?category=slug` - Filter by category
- `?recommendation=status` - Filter by recommendation status
- `?page=N` - Pagination

## Usage

### Adding a Supplier

1. Go to Wagtail Admin > Suppliers > Suppliers
2. Click "Add Supplier"
3. Fill in required fields (name, slug, category, description)
4. Set recommendation status and add notes explaining why
5. Add contact details, services, special terms
6. Add insurance/certification information
7. Save

### Managing Reviews

1. Go to Wagtail Admin > Suppliers > Reviews
2. Reviews must be manually created by admin (no public submission form yet)
3. Fill in group name, reviewer details, service used
4. Provide ratings (any combination of value, quality, service)
5. Add experience summary and optional detailed feedback
6. Check "Approved for display" to make it public
7. Save

**Note:** The average rating is automatically calculated and cannot be edited manually.

### Setting Up the Supplier List Page

1. In Wagtail admin, create a new page under your site root
2. Choose "Supplier List Page" as the page type
3. Set title (e.g., "Recommended Suppliers") and slug
4. Add an introduction text
5. Publish

There should only be one SupplierListPage per site.

## Admin Features

### Supplier ViewSet
- **List display**: name, category, recommendation status, last updated
- **Filters**: category, recommendation status, insurance status
- **Search**: name, description, services
- **Export**: CSV export of key fields

### Review ViewSet
- **List display**: supplier, group, date, average rating, approval status
- **Filters**: approval status, would use again, supplier, date
- **Search**: supplier name, group name, experience summary
- **Export**: CSV export including ratings and recommendations

## Templates

### Components
- `components/suppliers/supplier_card.html` - Card for supplier list
- `components/suppliers/review_card.html` - Card for individual review
- `components/navigation/pagination.html` - Pagination (updated to avoid variable collision)

### Pages
- `pages/suppliers/supplier_list_page.html` - Main list page with filters
- `pages/suppliers/supplier_detail.html` - Individual supplier detail with reviews

## Technical Notes

### Search Implementation
Uses Wagtail's search framework (not simple SQL LIKE queries) for better performance and relevance.

### Query Optimisation
- Uses `select_related()` for foreign keys (category, approved_by)
- Uses `prefetch_related()` for reverse relations (reviews)
- Annotates review statistics at query level to avoid N+1 queries

### Review Count Behaviour
`positive_review_count` and `negative_review_count` may not sum to `review_count` because some reviews may have `would_use_again=null` (reviewer was unsure).

### Generated Fields
The `average_rating` field uses Django's `GeneratedField` (Django 5.0+) which is calculated at the database level and persisted. This means:
- No need to update it manually
- Always consistent
- Efficient for queries/aggregations
- Cannot be edited directly

### Permissions
Uses standard Wagtail snippet permissions. Configure in Settings > Groups.

## Future Enhancements

Possible additions:
- Public review submission form with notification workflow
- Star rating visualisations
- Supplier comparison feature
- Email notifications when new reviews are submitted
- Automatic review reminder emails based on `review_due_date`
- Map integration for supplier locations
- File attachments (certificates, sample products)
