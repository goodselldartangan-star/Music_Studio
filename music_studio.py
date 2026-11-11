"""Music Studio: original lyrics + composition planning + vocal song rendering.

No uploaded reference audio or generated songs are sent to a third party by
this program. Only the approved JSON plan is sent to the music provider.
The optional GPT planner sends the textual concept and style profile only.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROFILES: dict[str, dict[str, Any]] = {
    "indie_pop_rock": {
        "description": "Rhythmic, guitar-led alternative pop with expressive lead singing and story-first lyrics",
        "bpm_range": [100, 120],
        "lead_voice": "expressive, intimate-to-powerful male lead vocal with believable breaths and phrasing",
        "positive_styles": ["indie alternative pop-rock", "rhythmic muted electric guitar and warm bass", "organic live-feel drums", "dynamic gritty expressive male lead vocals", "strong memorable chorus hook", "intimate conversational narrative lyrics", "professional detailed studio production"],
        "negative_styles": ["robotic singing", "unintelligible lyrics", "generic EDM drop", "overcompressed harsh master", "soundalikes"],
    },
    "electronic_story_pop": {
        "description": "Atmospheric melodic electronic pop with intimate female singing, pulsing bass and intricate arpeggios",
        "bpm_range": [115, 135],
        "lead_voice": "close, breathy, warm female lead vocal with a soft spoken-to-sung delivery",
        "positive_styles": ["cinematic narrative electronic pop", "pulsating analog synth bass and rippling arpeggios", "sparkling plucked synth", "deep crisp electronic drums", "ethereal intimate female vocals", "spacious atmospheric transition sound design", "strong repeated chorus hook", "professional wide and warm mix"],
        "negative_styles": ["shouty lead vocals", "muddy subbass", "harsh high frequencies", "generic EDM drop", "soundalikes"],
    },
    "hybrid": {
        "description": "Modern narrative pop blending organic guitar/bass with cinematic synths and expressive vocals",
        "bpm_range": [108, 128],
        "lead_voice": "distinctive emotional lead vocal, intimate in verses and powerful in choruses",
        "positive_styles": ["modern organic-electronic alternative pop", "syncopated guitar or plucked synth riff", "round warm bass", "punchy live-electronic hybrid drums", "expressive emotional singing", "organic dynamics and spacious electronic atmospheres", "narrative lyrics", "unforgettable recurring chorus"],
        "negative_styles": ["robotic vocals", "generic four-chord demo", "extreme clipping", "soundalikes"],
    },
}

OPENAI_URL = "https://api.openai.com/v1/responses"
MUSIC_URL = "https://api.elevenlabs.io/v1/music?output_format=mp3_48000_192"


def http_request(url: str, payload: dict[str, Any], header: str, secret: str) -> Request:
    return Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   headers={"Content-Type": "application/json", header: secret}, method="POST")


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate our metadata and the provider's published music_v2_5 plan contract."""
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object")
    if not isinstance(plan.get("title"), str) or not plan["title"].strip():
        raise ValueError("Plan needs a song title")
    if plan.get("profile") not in PROFILES:
        raise ValueError("Unknown style profile")
    if not isinstance(plan.get("bpm"), int) or not 70 <= plan["bpm"] <= 170:
        raise ValueError("BPM must be an integer between 70 and 170")
    chunks = plan.get("chunks")
    if not isinstance(chunks, list) or not 4 <= len(chunks) <= 30:
        raise ValueError("Use 4–30 song sections")
    total = 0
    names: list[str] = []
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Chunk {i} must be an object")
        text = chunk.get("text")
        if not isinstance(text, str) or not re.match(r"^\[[^\]]+\]", text.strip()):
            raise ValueError(f"Chunk {i}: text must start with [Section]")
        names.append(text.strip().splitlines()[0].lower())
        duration = chunk.get("duration_ms")
        if not isinstance(duration, int) or not 3000 <= duration <= 120000:
            raise ValueError(f"Chunk {i}: duration_ms must be 3000–120000")
        total += duration
        for style_key in ("positive_styles", "negative_styles"):
            styles = chunk.get(style_key)
            if not isinstance(styles, list) or len(styles) > 50 or any(not isinstance(s, str) or not s.strip() for s in styles):
                raise ValueError(f"Chunk {i}: {style_key} must be a list of 0–50 nonempty strings")
        if chunk.get("context_adherence", "high") not in ("low", "medium", "high"):
            raise ValueError(f"Chunk {i}: invalid context_adherence")
    if not 120000 <= total <= 360000:
        raise ValueError("Studio song must total 2–6 minutes")
    if not any("verse" in name for name in names) or not any("chorus" in name for name in names):
        raise ValueError("Sung songs need at least one verse and one chorus")
    for ch in chunks:
        if "chorus" in ch["text"].splitlines()[0].lower() and len(ch["text"].splitlines()) < 3:
            raise ValueError("Chorus must contain original singable lyrics, not just the label")
    return {"title": plan["title"], "profile": plan["profile"], "bpm": plan["bpm"],
            "duration_seconds": total / 1000, "sections": len(chunks)}


def music_payload(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    allowed = ("text", "duration_ms", "positive_styles", "negative_styles", "context_adherence")
    chunks = [{k: v for k, v in ch.items() if k in allowed} for ch in plan["chunks"]]
    return {"model_id": "music_v2_5", "composition_plan": {"chunks": chunks}}


def writing_brief(concept: str, profile: str, duration_seconds: int = 220) -> str:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    if not concept.strip():
        raise ValueError("A unique song concept is required")
    s = PROFILES[profile]
    return (f"Create a fully ORIGINAL 3–5 minute English song for this premise: {concept.strip()}\n"
            f"Style profile: {profile}: {s['description']}. Tempo around {s['bpm_range']} BPM. "
            f"Lead voice: {s['lead_voice']}. Preferred styles: {', '.join(s['positive_styles'])}. "
            f"Avoid: {', '.join(s['negative_styles'])}. Target song length ~{duration_seconds} seconds.\n"
            "Return a single JSON object: title (string), profile (exact profile name), bpm (integer), "
            "chunks (4–30 elements). Each chunk must have text beginning with a square-bracket section "
            "name such as [Verse 1], followed by original lyrics (or label only for instrumental intro/outro); "
            "duration_ms (3000–120000); positive_styles and negative_styles (string arrays); "
            "context_adherence ('high'). Include an intro, 2 verses, at least 2 memorable matching choruses, "
            "a bridge, and an outro. Lyrics need unusual concrete visual details, truthful emotions, "
            "singable line length and internal rhyme where natural. Make verses conversational and choruses "
            "emotionally direct. Chorus lyrics should repeat consistently; add a final variation. Balance "
            "lyrics against time so they can be sung, leaving room for instrumental breaks. Use the first "
            "chunk's positive_styles to establish the full sound. No covers, no references to actual artist "
            "names, no recycled lyrics or melodic copies. No markdown fences. Output JSON only.")


def parse_gpt_output(result: dict[str, Any]) -> dict[str, Any]:
    for item in result.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    plan = json.loads(part["text"])
                    validate_plan(plan)
                    return plan
    raise ValueError("GPT returned no plan JSON. Nothing was rendered or charged for music.")


def generate_plan(concept: str, profile: str, model: str | None = None, opener=urlopen) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY to use GPT planning, or prepare a plan JSON yourself")
    prompt = writing_brief(concept, profile)
    request = http_request(OPENAI_URL, {"model": model or os.environ.get("OPENAI_MODEL", "gpt-6"),
        "instructions": "You are a professional songwriter and arranger. Write original, structured songs and return valid JSON only.",
        "input": prompt, "text": {"format": {"type": "json_object"}}}, "Authorization", "Bearer " + api_key)
    with opener(request, timeout=90) as response:
        body = json.load(response)
    return parse_gpt_output(body)


def run_ffprobe(path: Path) -> dict[str, Any]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,sample_rate,channels", "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    obj = json.loads(result.stdout)
    audio = next((s for s in obj.get("streams", []) if s.get("codec_name") in ("mp3", "pcm_s16le", "pcm_s24le", "pcm_f32le", "aac", "flac", "opus")), None)
    if audio is None:
        raise ValueError("No recognized audio stream")
    return {"duration_seconds": float(obj["format"]["duration"]),
            "size_bytes": int(obj["format"].get("size", path.stat().st_size)),
            "codec": audio["codec_name"], "channels": int(audio["channels"]),
            "sample_rate": int(audio["sample_rate"])}


def volume_measure(path: Path) -> dict[str, float]:
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    if result.returncode:
        raise ValueError("Cannot decode audio file")
    values: dict[str, float] = {}
    for kind in ("mean", "max"):
        m = re.search(rf"{kind}_volume:\s*([+-]?(?:\d+(?:\.\d+)?|inf)) dB", result.stderr)
        if not m:
            raise ValueError(f"Cannot measure {kind} volume")
        values[kind + "_dbfs"] = float(m.group(1))
    return values


def quality_gate(path: Path, expected_seconds: float | None = None) -> dict[str, Any]:
    meta = run_ffprobe(path)
    if meta["duration_seconds"] < 3 or meta["channels"] < 1 or meta["sample_rate"] < 22050:
        raise ValueError("Invalid or suspicious audio format")
    if meta["size_bytes"] < 12_000:
        raise ValueError("File too small for a song")
    if expected_seconds is not None and abs(meta["duration_seconds"]-expected_seconds) > max(8, expected_seconds*.08):
        raise ValueError("Rendered duration differs too much from composition plan")
    levels = volume_measure(path)
    if not math.isfinite(levels["mean_dbfs"]) or levels["mean_dbfs"] < -42:
        raise ValueError("Audio is silent or too quiet")
    # MP3 decoder overshoots and 16-bit volumedetect rounding prevent precise
    # true-peak/clip validation. Flag possible overs rather than claiming certainty.
    warnings = []
    if levels["max_dbfs"] >= -0.1:
        warnings.append("Near digital full scale; review true peaks and audible distortion")
    return {"passed": True, **meta, **levels, "warnings": warnings,
            "human_listening_required": True}


def inspect_reference(path: Path) -> dict[str, Any]:
    """Local metadata only. Reference MP3 is never uploaded to a provider."""
    return {"filename": path.name, **run_ffprobe(path), **volume_measure(path),
            "note": "Descriptive only; derive style traits without copying lyrics, voices or melody."}


def render_music(plan: dict[str, Any], out: Path, *, dry_run: bool = False, opener=urlopen) -> dict[str, Any]:
    body = music_payload(plan)  # All invalid requests stop before accessing the API.
    if dry_run:
        return {"mode": "dry_run", "endpoint": MUSIC_URL, "request": body, "expected_seconds": sum(c["duration_ms"] for c in plan["chunks"])/1000}
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("Set ELEVENLABS_API_KEY to render music; no provider request was made")
    request = http_request(MUSIC_URL, body, "xi-api-key", key)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Never publish a partial or untested file. A provider error keeps the prior file intact.
    temp_path = out.with_suffix(out.suffix + ".partial")
    try:
        with opener(request, timeout=300) as response, temp_path.open("wb") as f:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                f.write(chunk)
        qa = quality_gate(temp_path, expected_seconds=sum(c["duration_ms"] for c in plan["chunks"])/1000)
        out.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp_path, out)
        return {"mode": "rendered", "path": str(out), "qa": qa}
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Original sung song studio with gated tests")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("profiles", help="List local reference-inspired style profiles")
    p = sub.add_parser("inspect", help="Inspect an audio file locally; never uploads it")
    p.add_argument("file", type=Path)
    p = sub.add_parser("brief", help="Prepare a GPT songwriting instruction without API access")
    p.add_argument("--profile", choices=PROFILES, required=True)
    p.add_argument("--concept", required=True)
    p = sub.add_parser("plan", help="Create an original vocal song plan using GPT (requires API key)")
    p.add_argument("--profile", choices=PROFILES, required=True)
    p.add_argument("--concept", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", default=None)
    p = sub.add_parser("validate-plan", help="Validate plan locally, with no network or charges")
    p.add_argument("file", type=Path)
    p = sub.add_parser("render", help="Render plan via ElevenLabs Music v2.5; requires API key")
    p.add_argument("file", type=Path)
    p.add_argument("--out", type=Path, default=Path("output/song.mp3"))
    p.add_argument("--dry-run", action="store_true", help="Print provider request, do not make paid call")
    p = sub.add_parser("qa", help="Verify audio container, duration, non-silence and levels")
    p.add_argument("file", type=Path)
    p.add_argument("--expected-seconds", type=float, default=None)
    a = parser.parse_args(argv)
    try:
        if a.command == "profiles":
            result = PROFILES
        elif a.command == "inspect":
            result = inspect_reference(a.file)
        elif a.command == "brief":
            result = {"brief": writing_brief(a.concept, a.profile)}
        elif a.command == "plan":
            plan = generate_plan(a.concept, a.profile, a.model)
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
            result = {"plan_file": str(a.out), **validate_plan(plan)}
        elif a.command == "validate-plan":
            result = validate_plan(json.loads(a.file.read_text()))
        elif a.command == "render":
            result = render_music(json.loads(a.file.read_text()), a.out, dry_run=a.dry_run)
        elif a.command == "qa":
            result = quality_gate(a.file, a.expected_seconds)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError, subprocess.CalledProcessError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Music Studio check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
