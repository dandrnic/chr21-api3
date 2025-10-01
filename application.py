"""WSGI entrypoint for platforms expecting `application` variable."""

from main import app as application

__all__ = ["application"]
