"""Storyboard model and validation against the component registry."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from . import registry
from .components import load_all

MAX_SCENES = 12
WORDS_PER_SECOND = 2.6
MIN_SCENE_S = 4.0
MAX_SCENE_S = 18.0
MAX_TOTAL_S = 150.0


class Scene(BaseModel):
    component: str
    params: dict[str, Any] = Field(default_factory=dict)
    narration: str = Field(default="", max_length=400)


class Storyboard(BaseModel):
    title: str = Field(max_length=120)
    scenes: list[Scene] = Field(min_length=1, max_length=MAX_SCENES)




def _sentence(text: str) -> str:
    """Make ``text`` end in punctuation, so the voice pauses after it instead of running into the next sentence."""
    text = text.strip()
    return text if not text or text[-1] in ".!?:;" else text + "."


CALLOUT_LEAD = {"takeaway": "Key takeaway:", "definition": "Definition:", "warning": "Warning:"}


def spoken_text(scene: Scene) -> str:
    """What the voice says for a scene: the narration, and nothing else. People do not read their slides aloud, so a
    callout's text is NOT recited after the narration: the planner is told to put the takeaway in the narration in its
    own words. Two exceptions keep a scene from being cut off or silent. A callout whose narration is empty speaks its
    key concept, and one whose narration ends in a colon (a lead-in like "So, in one line:") speaks it right after.
    The opening title_card speaks its title only when it has no narration; with narration, that is the hook, a curious
    question spoken in place of the written title. Keep worker/src/split.ts in step (tests/fixtures/split_parity.json)."""
    narration = scene.narration.strip()
    if scene.component == "callout" and (not narration or narration.endswith(":")):
        text = str(scene.params.get("text") or "").strip()
        if text:
            lead = CALLOUT_LEAD.get(str(scene.params.get("kind") or "takeaway"), CALLOUT_LEAD["takeaway"])
            return " ".join(p for p in (_sentence(narration), f"{lead} {_sentence(text)}") if p)
    if scene.component == "title_card" and not narration:
        return _sentence(str(scene.params.get("title") or "").strip())
    return narration


def scene_duration(narration: str) -> float:
    words = len(narration.split())
    return max(MIN_SCENE_S, min(MAX_SCENE_S, words / WORDS_PER_SECOND + 1.5))


def validate(raw: Any) -> tuple[Storyboard | None, list[str]]:
    """Validate a raw dict. Returns (storyboard with cleaned params, errors)."""
    load_all()
    try:
        sb = Storyboard.model_validate(raw)
    except ValidationError as e:
        return None, [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]

    errors: list[str] = []
    for i, scene in enumerate(sb.scenes):
        comp = registry.get(scene.component)
        if comp is None:
            errors.append(f"scenes[{i}]: unknown component '{scene.component}'")
            continue
        clean, errs = registry.validate_params(comp, scene.params)
        errors.extend(f"scenes[{i}] ({scene.component}): {e}" for e in errs)
        scene.params = clean
    total = sum(scene_duration(spoken_text(s)) for s in sb.scenes)
    if total > MAX_TOTAL_S:
        errors.append(f"video too long: ~{total:.0f}s estimated, max {MAX_TOTAL_S:.0f}s (shorten narration or use fewer scenes)")
    return (sb if not errors else None), errors
