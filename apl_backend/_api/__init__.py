"""Public API hosting component of the backend.

The API is hosted in a separate thread which is hosted by and
communicated with through the ``ApiHost`` class.
"""

from ._server import ApiHost

__all__ = [
    'ApiHost'
]
