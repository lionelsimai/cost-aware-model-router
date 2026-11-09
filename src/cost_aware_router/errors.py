"""Structured errors."""


class RouterError(Exception):
    """Base router error."""


class ProviderError(RouterError):
    """Raised by a model provider on failure (triggers fallback)."""


class AllProvidersFailedError(RouterError):
    """Raised when the whole fallback chain fails."""
