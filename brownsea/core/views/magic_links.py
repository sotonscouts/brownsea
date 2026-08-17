from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from wagtail.models import Page

from brownsea.core.magic_links import build_magic_link_url
from brownsea.core.models import PageAccessLevel, PageMagicLink


def _page_supports_magic_links(page):
    specific_page = page.specific
    if not hasattr(specific_page, "get_effective_access_level"):
        return False
    return (
        specific_page.access_level == PageAccessLevel.MAGIC_LINK
        or specific_page.get_effective_access_level() == PageAccessLevel.MAGIC_LINK
    )


def _get_editable_page(request, page_id, *, require_magic_link_access=False):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied
    if require_magic_link_access and not _page_supports_magic_links(page):
        raise PermissionDenied
    return page


def _get_magic_links_context(page, request):
    magic_links = PageMagicLink.objects.filter(page=page)
    active_links = list(magic_links.active())
    inactive_links = [link for link in magic_links if not link.is_active]
    return {
        "page": page,
        "magic_links": magic_links,
        "active_links": active_links,
        "inactive_links": inactive_links,
    }


def _redirect_after_action(request, page):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return None
    if request.POST.get("next") == "admin" or request.GET.get("next") == "admin":
        return redirect(reverse("wagtailadmin_pages:edit", args=[page.id]))
    return redirect(page.url)


@login_required
def magic_links_panel(request, page_id):
    page = _get_editable_page(request, page_id, require_magic_link_access=True)
    return render(
        request,
        "components/magic_links/modal.html",
        _get_magic_links_context(page, request),
    )


@login_required
@require_POST
def magic_links_create(request, page_id):
    page = _get_editable_page(request, page_id, require_magic_link_access=True)

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

    redirect_response = _redirect_after_action(request, page)
    if redirect_response is not None:
        return redirect_response

    return magic_links_panel(request, page_id)


@login_required
@require_POST
def magic_links_revoke(request, page_id, token_id):
    page = _get_editable_page(request, page_id, require_magic_link_access=True)
    magic_link = get_object_or_404(PageMagicLink, page=page, token_id=token_id)
    magic_link.revoke()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(status=204)

    redirect_response = _redirect_after_action(request, page)
    if redirect_response is not None:
        return redirect_response

    return magic_links_panel(request, page_id)
