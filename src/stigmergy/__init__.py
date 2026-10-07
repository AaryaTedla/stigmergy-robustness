"""Clean simulator package for the capstone's first implementation milestone.

The public environment and validated configuration live in environment.py.
Run `python -m stigmergy.cli demo` for a scripted mechanics demonstration.
This package does not yet implement learned policies, attacks, or defenses.
"""

from .environment import GridConfig, ResourceRetrievalEnv

__all__ = ["GridConfig", "ResourceRetrievalEnv"]
