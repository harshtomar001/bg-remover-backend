from typing import Any

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import settings


class GoogleTokenVerificationError(Exception):
    """Raised when a Google ID token is invalid."""


class GoogleAuthConfigurationError(Exception):
    """Raised when Google authentication is not configured."""


def verify_google_token(credential: str) -> dict[str, Any]:
    """
    Verify a Google ID token and return its trusted claims.

    Validates:
    - Token signature
    - Token expiration
    - Token issuer
    - Token audience
    - Verified email address
    """

    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthConfigurationError(
            "Google authentication is not configured."
        )

    if not credential or not credential.strip():
        raise GoogleTokenVerificationError(
            "Google credential is missing."
        )

    try:
        payload = id_token.verify_oauth2_token(
            credential,
            Request(),
            audience=settings.GOOGLE_CLIENT_ID,
        )

    except (ValueError, google.auth.exceptions.GoogleAuthError) as exc:
        raise GoogleTokenVerificationError(
            "Invalid or expired Google ID token."
        ) from exc

    # Google's stable account identifier.
    google_sub = payload.get("sub")

    # Normalize the verified email.
    email = payload.get("email")

    if not google_sub or not email:
        raise GoogleTokenVerificationError(
            "Google token is missing required identity information."
        )

    if payload.get("email_verified") is not True:
        raise GoogleTokenVerificationError(
            "Google email address is not verified."
        )

    return {
        "google_sub": google_sub,
        "email": email.strip().lower(),
        "name": payload.get("name"),
    }