import uuid

from django.core.signing import BadSignature, Signer

from brownsea.core.models import PageAccessLevel, PageMagicLink

MAGIC_LINK_SESSION_KEY = "brownsea_magic_link_ids"
MAGIC_LINK_SIGNER_SALT = "brownsea.page-magic-link"


def get_signer() -> Signer:
    return Signer(salt=MAGIC_LINK_SIGNER_SALT)


def sign_magic_link(magic_link: PageMagicLink) -> str:
    return get_signer().sign(str(magic_link.token_id))


def unsign_magic_link_token(token: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(get_signer().unsign(token))
    except (BadSignature, ValueError):
        return None


def get_magic_link_for_token(token: str) -> PageMagicLink | None:
    token_id = unsign_magic_link_token(token)
    if token_id is None:
        return None

    try:
        return PageMagicLink.objects.select_related("page").get(token_id=token_id)
    except PageMagicLink.DoesNotExist:
        return None


def build_magic_link_url(magic_link: PageMagicLink, request=None) -> str:
    page_url = magic_link.page.get_url(request) if request else magic_link.page.url
    return f"{page_url}?access={sign_magic_link(magic_link)}"


def get_session_magic_link_ids(request) -> list[str]:
    return list(request.session.get(MAGIC_LINK_SESSION_KEY, []))


def grant_magic_link_access(request, magic_link: PageMagicLink) -> None:
    link_ids = get_session_magic_link_ids(request)
    token_id = str(magic_link.token_id)
    if token_id not in link_ids:
        link_ids.append(token_id)
        request.session[MAGIC_LINK_SESSION_KEY] = link_ids


def get_active_session_magic_links(request) -> list[PageMagicLink]:
    active_links = []
    active_ids = []

    for token_id in get_session_magic_link_ids(request):
        try:
            magic_link = PageMagicLink.objects.select_related("page").get(token_id=token_id)
        except PageMagicLink.DoesNotExist:
            continue

        if magic_link.is_active:
            active_links.append(magic_link)
            active_ids.append(token_id)

    if active_ids != get_session_magic_link_ids(request):
        request.session[MAGIC_LINK_SESSION_KEY] = active_ids

    return active_links


def magic_link_covers_page(magic_link: PageMagicLink, page) -> bool:
    return page.path.startswith(magic_link.page.path)


def has_magic_link_access(request, page) -> bool:
    if page.get_effective_access_level() != PageAccessLevel.MAGIC_LINK:
        return False

    for magic_link in get_active_session_magic_links(request):
        if magic_link_covers_page(magic_link, page):
            return True

    return False


def redeem_magic_link_token(request, token: str, page) -> bool:
    magic_link = get_magic_link_for_token(token)
    if magic_link is None or not magic_link.is_active:
        return False

    if not magic_link_covers_page(magic_link, page):
        return False

    if page.get_effective_access_level() != PageAccessLevel.MAGIC_LINK:
        return False

    grant_magic_link_access(request, magic_link)
    return True
