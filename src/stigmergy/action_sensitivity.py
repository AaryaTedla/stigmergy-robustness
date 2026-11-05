"""Summarize a full PPO policy's local sensitivity to pheromone inputs.

This Phase 2A diagnostic answers a narrow question left open by delivery-only
scores: when a frozen full-input policy encounters pheromone in its ordinary
58-value local observation, do its action probabilities change if only the 18
food/home pheromone values are hidden?  It never changes an environment,
checkpoint, reward, or rollout action.  The comparison is a counterfactual
read of the same local policy input, and is therefore evidence of input
sensitivity rather than proof of causal coordination or a Phase 2B detector.

``LocalActionSensitivity`` accepts paired categorical action-probability rows
for every policy observation.  It reports total-variation distance (half the
L1 difference), the fraction of rows whose most likely action changes, and
the same values restricted to rows where at least one local pheromone value is
nonzero.  Probability rows are finite nonnegative vectors with a shared action
count; callers supply the visibility mask derived only from the local input.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class LocalActionSensitivity:
    """Accumulate action-distribution differences for full and masked inputs.

    ``update`` operates on any leading batch shape after flattening it to rows.
    It intentionally retains aggregate counts only, so a report cannot become
    an unbounded trajectory store or expose simulator-only state.  An action
    distribution's total-variation distance is bounded in ``[0, 1]``: zero
    means masking pheromone did not change the distribution and one means the
    distributions have no overlapping probability mass.
    """

    observations: int = 0
    visible_observations: int = 0
    total_variation_sum: float = 0.0
    visible_total_variation_sum: float = 0.0
    argmax_changed: int = 0
    visible_argmax_changed: int = 0
    action_count: int | None = None

    def update(self, full_probabilities, masked_probabilities, pheromone_visible):
        """Add one batch of paired categorical policy probabilities.

        Parameters
        ----------
        full_probabilities, masked_probabilities:
            Finite arrays ending in the same positive action dimension.  Every
            row must be nonnegative and sum to one within a small float error.
        pheromone_visible:
            Boolean mask matching the leading probability dimensions.  ``True``
            identifies a row with a nonzero local food or home pheromone value.
        """
        full = np.asarray(full_probabilities, dtype=np.float64)
        masked = np.asarray(masked_probabilities, dtype=np.float64)
        if full.ndim < 1 or full.shape != masked.shape or full.shape[-1] < 1:
            raise ValueError("paired probability arrays must share a positive final action dimension")
        if not np.isfinite(full).all() or not np.isfinite(masked).all():
            raise ValueError("probabilities must be finite")
        if (full < 0).any() or (masked < 0).any():
            raise ValueError("probabilities must be nonnegative")
        if not (np.allclose(full.sum(axis=-1), 1.0, atol=1e-5) and
                np.allclose(masked.sum(axis=-1), 1.0, atol=1e-5)):
            raise ValueError("each probability row must sum to one")
        visible = np.asarray(pheromone_visible, dtype=bool)
        if visible.shape != full.shape[:-1]:
            raise ValueError("pheromone_visible must match probability leading dimensions")
        actions = full.shape[-1]
        if self.action_count is not None and self.action_count != actions:
            raise ValueError("all updates must use the same action count")
        self.action_count = actions
        full, masked, visible = full.reshape(-1, actions), masked.reshape(-1, actions), visible.reshape(-1)
        variation = 0.5 * np.abs(full - masked).sum(axis=1)
        changed = np.argmax(full, axis=1) != np.argmax(masked, axis=1)
        self.observations += len(variation)
        self.visible_observations += int(visible.sum())
        self.total_variation_sum += float(variation.sum())
        self.visible_total_variation_sum += float(variation[visible].sum())
        self.argmax_changed += int(changed.sum())
        self.visible_argmax_changed += int(changed[visible].sum())

    def summary(self):
        """Return JSON-safe aggregate sensitivity values, using zero for no rows."""
        return {
            "agent_observations": self.observations,
            "visible_agent_observations": self.visible_observations,
            "visible_fraction": self.visible_observations / self.observations if self.observations else 0.0,
            "mean_total_variation": self.total_variation_sum / self.observations if self.observations else 0.0,
            "visible_mean_total_variation": (self.visible_total_variation_sum / self.visible_observations
                                               if self.visible_observations else 0.0),
            "argmax_changed_fraction": self.argmax_changed / self.observations if self.observations else 0.0,
            "visible_argmax_changed_fraction": (self.visible_argmax_changed / self.visible_observations
                                                  if self.visible_observations else 0.0),
            "action_count": self.action_count or 0,
        }
