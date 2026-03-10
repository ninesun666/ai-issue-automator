"""
GitHub webhook signature verification.

This module provides functions to verify the authenticity of
GitHub webhook requests using HMAC-SHA256 signatures.
"""

import hmac
import hashlib
from typing import Optional


def verify_github_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload: Raw request body as bytes
        signature: Value of X-Hub-Signature-256 header (format: sha256=<hex>)
        secret: Webhook secret configured in GitHub

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> is_valid = verify_github_signature(
        ...     payload=request.body,
        ...     signature=request.headers.get("X-Hub-Signature-256"),
        ...     secret="my-webhook-secret"
        ... )
    """
    if not signature or not secret:
        return False

    # Extract the hex digest from the signature header
    # Format: sha256=<hex_digest>
    if not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]  # Remove 'sha256=' prefix

    # Compute the HMAC-SHA256 hash
    computed_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_signature, expected_signature)


def compute_signature(payload: bytes, secret: str) -> str:
    """
    Compute GitHub webhook signature for testing purposes.

    Args:
        payload: Raw request body as bytes
        secret: Webhook secret

    Returns:
        Signature string in format: sha256=<hex_digest>
    """
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"
