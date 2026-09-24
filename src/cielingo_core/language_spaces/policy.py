"""CIELingo language trajectory policy v1.1E + HE research candidate.

This module is intentionally small and non-invasive. It does not remove any
regional solver. It marks which regional surfaces are allowed to grow by default.

Policy as of 2026-05-30:
    - PL is the primary CIELingo work axis.
    - EN is allowed to evolve as-needed / as-we-go.
    - JA is temporarily frozen for new growth and excluded from default probes
      until explicit review/approval reopens it.

Research extension as of 2026-09-23:
    - HE is a bounded research-candidate surface for Semitic root-pattern and
      orbital-semantic experiments. It is excluded from default probes and
      requires review before expansion.

Boundary:
    This policy is not SOURCE/canon promotion, not NOEMA writeback authority,
    and not a semantic identity or physical-binding claim.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

LanguageId = Literal["pl", "en", "ja", "he"]


@dataclass(frozen=True)
class LanguageTrajectory:
    language_id: LanguageId
    priority: str
    growth_mode: str
    default_probe_enabled: bool
    new_feature_growth_allowed: bool
    requires_review_before_expansion: bool
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


LANGUAGE_TRAJECTORY: dict[str, LanguageTrajectory] = {
    "pl": LanguageTrajectory(
        language_id="pl",
        priority="primary",
        growth_mode="main_axis",
        default_probe_enabled=True,
        new_feature_growth_allowed=True,
        requires_review_before_expansion=False,
        note="Polish is the primary CIELingo development and validation surface.",
    ),
    "en": LanguageTrajectory(
        language_id="en",
        priority="secondary",
        growth_mode="as_we_go",
        default_probe_enabled=True,
        new_feature_growth_allowed=True,
        requires_review_before_expansion=False,
        note="English evolves only when real usage/probe pressure requires it.",
    ),
    "ja": LanguageTrajectory(
        language_id="ja",
        priority="parked",
        growth_mode="temporarily_frozen",
        default_probe_enabled=False,
        new_feature_growth_allowed=False,
        requires_review_before_expansion=True,
        note="Japanese is temporarily closed for new CIELingo growth and excluded from default probes until explicit review.",
    ),
    "he": LanguageTrajectory(
        language_id="he",
        priority="research",
        growth_mode="research_candidate",
        default_probe_enabled=False,
        new_feature_growth_allowed=True,
        requires_review_before_expansion=True,
        note="Hebrew is a bounded Semitic research surface for root-pattern, vocalization and orbital-semantic validation; it is not a default probe or canon source.",
    ),
}


def get_language_trajectory(language_id: str) -> LanguageTrajectory:
    try:
        return LANGUAGE_TRAJECTORY[language_id]
    except KeyError as exc:
        raise ValueError(f"unknown language_id: {language_id}") from exc


def default_probe_languages() -> tuple[str, ...]:
    return tuple(lang for lang, cfg in LANGUAGE_TRAJECTORY.items() if cfg.default_probe_enabled)


def language_policy_snapshot() -> dict[str, dict[str, object]]:
    return {lang: cfg.to_dict() for lang, cfg in sorted(LANGUAGE_TRAJECTORY.items())}
