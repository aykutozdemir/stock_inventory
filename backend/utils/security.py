"""
Security utilities
Provides functions for input sanitization, XSS protection, and security helpers.
"""
import html
import re
from typing import Any, Union

def sanitize_input(value: Any) -> Union[str, Any]:
    """
    Sanitize user input to prevent injection attacks
    Removes potentially dangerous characters and patterns
    """
    if not isinstance(value, str):
        return value

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove control characters (except newlines and tabs)
    value = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)

    # Remove potential SQL injection patterns (basic protection)
    # This is additional protection, but parameterized queries are primary defense
    dangerous_patterns = [
        r';\s*(drop|delete|update|insert|alter|create)\s',
        r'/\*.*\*/',  # Block comments
        r'--.*',      # Line comments
        r'union\s+select',
        r'information_schema',
        r'load_file\s*\(',
        r'into\s+outfile',
    ]

    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    return value

def escape_html(value: Any) -> Union[str, Any]:
    """
    Escape HTML characters to prevent XSS attacks
    """
    if not isinstance(value, str):
        return value

    return html.escape(value, quote=True)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks
    """
    if not filename:
        return ''

    # Remove path separators
    filename = re.sub(r'[\/\\]', '', filename)

    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            filename = name[:250] + '.' + ext[:4]
        else:
            filename = filename[:255]

    return filename

def validate_url(url: str) -> bool:
    """
    Basic URL validation
    """
    if not url:
        return False

    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

    return url_pattern.match(url) is not None

def check_file_signature(file_content: bytes, allowed_types: list) -> bool:
    """
    Check file signature/magic bytes to verify file type
    Args:
        file_content: File content as bytes
        allowed_types: List of allowed MIME types
    """
    if not file_content:
        return False

    # Magic byte signatures for common file types
    signatures = {
        'image/jpeg': [b'\xff\xd8\xff'],
        'image/png': [b'\x89PNG\r\n\x1a\n'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'image/webp': [b'RIFF', b'WEBP'],  # WebP has RIFF header
        'application/pdf': [b'%PDF-'],
    }

    # Check file signatures
    for mime_type in allowed_types:
        if mime_type in signatures:
            for signature in signatures[mime_type]:
                if file_content.startswith(signature):
                    return True

    return False

def rate_limit_check(identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """
    Basic rate limiting check
    Note: This is a simple in-memory implementation.
    For production, use Redis or similar.
    """
    # This is a simplified implementation
    # In production, you'd want to use Redis or a database
    import time
    from collections import defaultdict

    # Simple in-memory rate limiting (not suitable for multi-process/production)
    if not hasattr(rate_limit_check, '_requests'):
        rate_limit_check._requests = defaultdict(list)

    current_time = time.time()
    requests = rate_limit_check._requests[identifier]

    # Remove old requests outside the window
    requests[:] = [req_time for req_time in requests
                   if current_time - req_time < window_seconds]

    # Check if under limit
    if len(requests) >= max_requests:
        return False

    # Add current request
    requests.append(current_time)
    return True

def generate_csrf_token() -> str:
    """
    Generate a CSRF token
    """
    import secrets
    return secrets.token_urlsafe(32)

def validate_csrf_token(session_token: str, received_token: str) -> bool:
    """
    Validate CSRF token
    """
    if not session_token or not received_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(session_token, received_token)
