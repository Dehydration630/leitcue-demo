"""Pure, synthetic portfolio examples. Not production orchestration or audio AI."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class Event:
    at_ms: int
    kind: str
    persistent: bool = False
    evidence_bound: bool = False
    importance: int = 0


def cue_cap(duration_ms: int) -> int:
    if type(duration_ms) is not int or not 30_000 <= duration_ms <= 180_000:
        raise ValueError("episode_duration_out_of_range")
    return min(12, (duration_ms - 1) // 10_000)


def plan_cues(duration_ms: int, events: list[Event], chosen: list[int] | None = None):
    """Return half-open windows. None means automatic; [] means user chose one."""
    cap = cue_cap(duration_ms)
    if chosen is not None:
        if any(type(t) is not int for t in chosen):
            raise ValueError("invalid_boundary")
        boundaries = sorted(chosen)
        if len(set(boundaries)) != len(boundaries):
            raise ValueError("duplicate_boundary")
        points = [0, *boundaries, duration_ms]
        if len(points) - 1 > cap:
            raise ValueError("cue_count_exceeded")
        if any(b - a < 5000 for a, b in zip(points, points[1:])):
            raise ValueError("cue_too_short")
    else:
        # A bounded, readable heuristic, not the production merging algorithm.
        eligible = [e for e in events if e.kind in {"relationship_reset", "scene_reset"}
                    and e.persistent and e.evidence_bound
                    and 5000 <= e.at_ms <= duration_ms - 5000]
        boundaries = []
        for event in sorted(eligible, key=lambda e: (-e.importance, e.at_ms)):
            if len(boundaries) >= cap - 1:
                break
            if all(abs(event.at_ms - t) >= 5000 for t in boundaries):
                boundaries.append(event.at_ms)
        points = [0, *sorted(boundaries), duration_ms]
    return tuple(zip(points, points[1:]))


def resolve_identity(episode: dict, layers: list[dict]):
    resolved, provenance = dict(episode), {key: "episode" for key in episode}
    for layer in layers:
        if not layer.get("reason", "").strip():
            raise ValueError("override_requires_reason")
        if layer.get("scope") not in {"phase", "cue"}:
            raise ValueError("invalid_scope")
        for key, value in layer["values"].items():
            if key not in episode:
                raise ValueError("unknown_identity_field")
            resolved[key], provenance[key] = value, layer["scope"]
    return resolved, provenance


def compile_music(identity: dict, *, carrier: str, energy: str, first: bool,
                  character_presence: str = "unknown"):
    if carrier not in {"rhythm", "atmosphere", "motif"}:
        raise ValueError("unknown_carrier")
    if energy not in {"low", "medium", "high"}:
        raise ValueError("unknown_energy")
    if character_presence not in {"present", "absent", "unknown"}:
        raise ValueError("unknown_presence")
    hook = first and character_presence != "absent"
    effective_carrier = "rhythm" if hook else carrier
    provider = "stable_audio" if effective_carrier == "atmosphere" else "mureka"
    entry = "mature_rhythm" if hook else "established_texture" if carrier == "atmosphere" else "established_section"
    # Deliberately never says 'start at second zero with a perfect four-bar hook'.
    prompt = (f"Setting: {identity['setting']}; palette: {identity['palette']}. "
              f"{effective_carrier}-led, {energy} energy, sparse melody, breathing space. "
              "Instrumental only: no singing, humming, chanting or vocal samples.")
    return {"provider": provider, "prompt": prompt, "entry": entry,
            "voice": "instrumental", "carrier": effective_carrier, "energy": energy}


def group_sources(recipes: list[dict]):
    """All generation requirements must match; reset/unknown cues stay separate."""
    groups = {}
    for recipe in recipes:
        if recipe["cue_id"] in {c for group in groups.values() for c in group["cue_ids"]}:
            raise ValueError("duplicate_cue")
        contract = {k: v for k, v in recipe.items() if k not in {"cue_id", "reset", "unknown"}}
        if recipe.get("reset") or recipe.get("unknown"):
            contract["isolated_cue"] = recipe["cue_id"]
        key = sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
        group = groups.setdefault(key, {"recipe": contract, "cue_ids": []})
        group["cue_ids"].append(recipe["cue_id"])
    return tuple(groups.values())


def reserve_once(ledger: dict, key: str, amount: int, cap: int):
    """Integer demo units, NOT provider prices. Production requires transactions."""
    if not key or type(amount) is not int or amount < 0 or type(cap) is not int or cap < 0:
        raise ValueError("invalid_reservation")
    if key in ledger:
        if ledger[key]["amount"] != amount:
            raise ValueError("idempotency_conflict")
        return {**ledger[key], "created": False}
    if sum(item["amount"] for item in ledger.values()) + amount > cap:
        raise ValueError("budget_exceeded")
    ledger[key] = {"amount": amount, "state": "reserved"}
    return {**ledger[key], "created": True}


def may_submit(state: str) -> bool:
    # Unknown is not failed-before-submit; do not turn it into a new paid request.
    return state == "reserved"


def rank_excerpts(windows: list[dict], required_ms: int, track_ms: int):
    """Synthetic 0..1 proxies. Scores are rankings, never quality probabilities."""
    if required_ms <= 0 or track_ms <= 0:
        raise ValueError("invalid_duration")
    ranked = []
    for window in windows:
        start = window["start_ms"]
        if start < 0 or start + required_ms > track_ms:
            continue
        metrics = [window[k] for k in ("coverage", "rhythm", "stability", "exit_softness")]
        if any(not 0 <= value <= 1 for value in metrics):
            raise ValueError("invalid_proxy")
        coverage, rhythm, stability, exit_softness = metrics
        if coverage < .9:
            continue
        score = .3 * coverage + .35 * rhythm + .2 * stability + .15 * exit_softness
        ranked.append({**window, "score": round(score, 4)})
    return sorted(ranked, key=lambda w: (-w["score"], w["start_ms"]))[:3]
