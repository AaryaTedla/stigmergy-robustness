"""Clean simulator package for the capstone's first implementation milestone.

The public environment and validated configuration live in environment.py.
Run `python -m stigmergy.cli demo` for a scripted mechanics demonstration.
This package includes a bounded persistent attack/provenance pilot but no
learned policy, attack evaluation, or trained defense result.
"""

from .attacks import AttackConfig, PersistentFalseFoodInjector
from .environment import GridConfig, ResourceRetrievalEnv

__all__ = ["AttackConfig", "GridConfig", "PersistentFalseFoodInjector", "ResourceRetrievalEnv"]
