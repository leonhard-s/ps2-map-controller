"""Namespace for event handling subcomponents.

The submodules in this namespace should be considered independent and
should only rely on the parent controller module, not on each other.
"""

from ._base_ownership import BaseOwnershipController

__all__ = [
    'BaseOwnershipController',
]
