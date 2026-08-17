from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from wagtail.models import Page

from brownsea.core.magic_links import build_magic_link_url
from brownsea.core.models import PageAccessLevel, PageMagicLink


def _get_editable_page(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied
    if page.get_effective_access_level() != PageAccessLevel.MAGIC_LINK:
        raise PermissionDenied
    return page


@login_required
def magic_links_panel(request, page_id):
    page = _get_editable_page(request, page_id)
    magic_links = PageMagicLink.objects.filter(page=page)
    active_links = list(magic_links.active())
    inactive_links = [link for link in magic_links if not link.is_active]
    return render(
        request,
        "components/magic_links/modal.html",
        {
            "page": page,
            "magic_links": magic_links,
            "active_links": active_links,
            "inactive_links": inactive_links,
        },
    )


@login_required
@require_POST
def magic_links_create(request, page_id):
    page = _get_editable_page(request, page_id)

    label = request.POST.get("label", "").strip()
    expires_at_raw = request.POST.get("expires_at", "").strip()
    expires_at = parse_datetime(expires_at_raw) if expires_at_raw else None
    if expires_at is not None and timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())

    magic_link = PageMagicLink.objects.create(
        page=page,
        label=label,
        expires_at=expires_at,
        created_by=request.user,
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(
            request,
            "components/magic_links/link_row.html",
            {
                "link": magic_link,
                "share_url": build_magic_link_url(magic_link, request),
                "page": page,
            },
        )

    return magic_links_panel(request, page_id)


@login_required
@require_POST
def magic_links_revoke(request, page_id, token_id):
    page = _get_editable_page(request, page_id)
    magic_link = get_object_or_404(PageMagicLink, page=page, token_id=token_id)
    magic_link.revoke()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(status=204)

    return magic_links_panel(request, page_id)
