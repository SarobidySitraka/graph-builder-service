"""
Complete security utilities for authentication, authorization and validation.
Provides API key authentication, file validation, and security helpers.
"""
import secrets
import hashlib
import hmac
from typing import Optional, List
from datetime import datetime
from fastapi import Header, HTTPException, status, Request
from fastapi.security import APIKeyHeader

from app.core.config import settings

# ============================================================================
# API Key Authentication
# ============================================================================

api_key_header = APIKeyHeader(name=settings.api_key_name, auto_error=False)

def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.

    Args:
        length: Length of the key (default: 32 bytes)

    Returns:
        URL-safe base64 encoded key

    Example:
        >>> key = generate_api_key()
        >>> print(key)  # e.g., "x7F3k9Lm2Np8Qq1Rr5Tt6Vv7Ww8Xx9Yy0Zz"
    """
    return secrets.token_urlsafe(length)


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a secure secret key for cryptographic operations.

    Args:
        length: Length of the key in bytes (default: 32)

    Returns:
        Hexadecimal string representation

    Example:
        >>> key = generate_secret_key()
        >>> print(key)  # 64 character hex string
    """
    return secrets.token_hex(length)


async def verify_api_key(
        api_key: Optional[str] = Header(None, alias=settings.api_key_name)
) -> str:
    """
    Verify API key from request header.
    FastAPI dependency for endpoint protection.

    Args:
        api_key: API key from request header

    Returns:
        Verified API key

    Raises:
        HTTPException: If API key is missing or invalid

    Usage:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            return {"message": "Access granted"}
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def optional_api_key(
        api_key: Optional[str] = Header(None, alias=settings.api_key_name)
) -> Optional[str]:
    """
    Optional API key verification.
    Returns None if no key provided, validates if present.

    Args:
        api_key: Optional API key from request header

    Returns:
        Verified API key or None

    Raises:
        HTTPException: If API key is provided but invalid
    """
    if not api_key:
        return None

    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


# ============================================================================
# File Security
# ============================================================================

def check_file_extension(
        filename: str,
        allowed_extensions: Optional[List[str]] = None
) -> bool:
    """
    Check if file extension is allowed.

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: from settings)

    Returns:
        True if extension is allowed, False otherwise

    Example:
        >>> check_file_extension("data.csv")
        True
        >>> check_file_extension("script.exe")
        False
    """
    if allowed_extensions is None:
        allowed_extensions = settings.allowed_extensions

    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]


def get_file_extension(filename: str) -> Optional[str]:
    """
    Extract file extension from filename.

    Args:
        filename: Name of the file

    Returns:
        File extension (lowercase) or None

    Example:
        >>> get_file_extension("data.CSV")
        'csv'
    """
    if not filename or '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent security issues.

    Removes:
    - Path traversal attempts (../, ..\)
    - Directory separators (/, \)
    - Null bytes
    - Control characters

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("file\x00name.txt")
        'filename.txt'
    """
    if not filename:
        return "unnamed"

    # Remove any directory components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove null bytes and control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    filename = filename.replace('\x00', '')

    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '')

    # Limit length while preserving extension
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]

    # Ensure we still have a valid filename
    if not filename or filename in ['.', '..']:
        return "unnamed"

    return filename


def validate_file_size(size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size against maximum allowed.

    Args:
        size: File size in bytes
        max_size: Maximum size in bytes (default: from settings)

    Returns:
        True if size is valid, False otherwise

    Example:
        >>> validate_file_size(1024 * 1024)  # 1MB
        True
        >>> validate_file_size(200 * 1024 * 1024)  # 200MB
        False
    """
    if max_size is None:
        max_size = settings.max_upload_size

    return 0 < size <= max_size


# ============================================================================
# Content Security
# ============================================================================

def calculate_file_hash(content: bytes, algorithm: str = "sha256") -> str:
    """
    Calculate hash of file content.

    Args:
        content: File content as bytes
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        Hexadecimal hash string

    Example:
        >>> content = b"Hello, World!"
        >>> calculate_file_hash(content)
        'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(content)
    return hash_func.hexdigest()


def verify_hmac_signature(
        data: str,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
) -> bool:
    """
    Verify HMAC signature for data integrity.

    Args:
        data: Original data
        signature: Signature to verify
        secret: Secret key
        algorithm: HMAC algorithm

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> data = "important data"
        >>> sig = create_hmac_signature(data, "secret")
        >>> verify_hmac_signature(data, sig, "secret")
        True
    """
    expected_signature = hmac.new(
        secret.encode(),
        data.encode(),
        algorithm
    ).hexdigest()

    return secrets.compare_digest(signature, expected_signature)


def create_hmac_signature(
        data: str,
        secret: str,
        algorithm: str = "sha256"
) -> str:
    """
    Create HMAC signature for data.

    Args:
        data: Data to sign
        secret: Secret key
        algorithm: HMAC algorithm

    Returns:
        Hexadecimal signature string
    """
    return hmac.new(
        secret.encode(),
        data.encode(),
        algorithm
    ).hexdigest()


# ============================================================================
# Request Security
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Checks X-Forwarded-For header first (for proxies).

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (from proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    if request.client:
        return request.client.host

    return "unknown"


def is_safe_redirect_url(url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
    """
    Check if redirect URL is safe (prevents open redirect vulnerabilities).

    Args:
        url: URL to validate
        allowed_hosts: List of allowed hostnames

    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False

    # Relative URLs are safe
    if url.startswith('/') and not url.startswith('//'):
        return True

    # Check against allowed hosts
    if allowed_hosts:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts

    return False


# ============================================================================
# Session Security
# ============================================================================

def generate_session_id(length: int = 32) -> str:
    """
    Generate a secure session ID.

    Args:
        length: Length of the session ID

    Returns:
        URL-safe session ID
    """
    return secrets.token_urlsafe(length)


def is_session_expired(created_at: float, timeout: int) -> bool:
    """
    Check if session has expired.

    Args:
        created_at: Session creation timestamp
        timeout: Session timeout in seconds

    Returns:
        True if expired, False otherwise
    """
    return (datetime.now().timestamp() - created_at) > timeout