import time

import jwt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@login_required
@never_cache
def woodmap_token(request: HttpRequest) -> JsonResponse:
    """Issue a short-lived Woodmap API token for the logged-in user."""
    scopes = ["public", "internal"]
    if request.user.has_perm("standard_pages.view_restricted_map"):
        scopes.append("restricted")

    claims = {
        "sub": str(request.user.pk),
        "exp": int(time.time()) + settings.WOODMAP_JWT_TTL,
        "scope": " ".join(scopes),
    }
    if settings.WOODMAP_JWT_ISSUER:
        claims["iss"] = settings.WOODMAP_JWT_ISSUER
    if settings.WOODMAP_JWT_AUDIENCE:
        claims["aud"] = settings.WOODMAP_JWT_AUDIENCE

    token = jwt.encode(claims, settings.WOODMAP_JWT_SECRET, algorithm=settings.WOODMAP_JWT_ALGORITHM)
    return JsonResponse({"token": token})
