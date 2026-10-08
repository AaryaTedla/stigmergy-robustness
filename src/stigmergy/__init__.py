"""Clean simulator package for the capstone's first implementation milestone.

The public environment and validated configuration live in environment.py.
Run `python -m stigmergy.cli demo` for a scripted mechanics demonstration.
The package also includes a bounded persistent attack/provenance pilot.
Optional shared PPO training lives in training.py; its PyTorch/SB3 imports
are kept out of this initializer so simulator-only installations still work.
Short-run checkpoint evidence does not establish attack evaluation or a
trained defense result.
"""

from .attacks import AttackConfig, PersistentFalseFoodInjector
from .environment import GridConfig, ResourceRetrievalEnv

__all__ = ["AttackConfig", "GridConfig", "PersistentFalseFoodInjector", "ResourceRetrievalEnv"]
