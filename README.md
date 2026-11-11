# Music Studio v4 — offline GPT-composed music

Music Studio is an **offline, modular MIDI + Python DSP music engine**. GPT can write or edit a score, inspect machine-checkable music-theory feedback, and render a complete original MP3 without another generative AI, user key, subscription, or third-party music API.

Version 4 preserves the v3 synthesizer and its sound vocabulary while improving the composition/revision process. It intentionally **doesn't claim to listen** to audio like a human.

## Quick start

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python render.py --preview-bars 16 --score-only --out preview
python review_score.py preview/Blue_Hour_Signal.score.json --strict
python render.py --preview-bars 16 --out preview
python check.py preview --preview
python render.py --out output
python check.py output
```

`ffmpeg` and `ffprobe` must be installed. The output folder holds `Blue_Hour_Signal.mp3` (320 kbps), 24-bit WAV, MIDI, JSON score, `composition_review.json`, and `qa_report.json`.

## GPT-friendly boundaries

| File | Owns | Imports |
|---|---|---|
| `studio3/spec.py` | stable Note/Drum/Settings and song timeline | stdlib |
| `studio3/composition.py` | original motives, chord choices, and score creation | `spec` |
| `studio3/theory.py` | chord-pitch contracts, key and scale helpers | stdlib |
| `studio3/development.py` | pure score-level phrase variation | `theory` |
| `studio3/review.py` | score and repetition checks; prints actionable diagnostics | `theory` |
| `studio3/instruments.py` | waveform synthesis for one note or drum | `spec`, NumPy, SciPy |
| `studio3/mix.py` | routing, per-bus processing, stereo width, WAV | `spec`, `instruments`, NumPy/SciPy |
| `studio3/midi.py` | portable MIDI writer | Mido |
| `studio3/quality.py` | independent full/preview MP3+WAV acceptance gate | `review`, `composition`, audio tools |
| `render.py`, `review_score.py`, `check.py` | CLI facades, no DSP logic | relevant modules |

Edit a melody in `composition.py` or `development.py`, an instrument in `instruments.py`, mix width in `mix.py`, and acceptance conditions in `review.py` or `quality.py`. Avoid changing shared data structures unless a version is introduced. All old v2 and v3 source is retained for comparison.

## Compare before accepting a change

```bash
python render.py --preview-bars 48 --no-development --stereo-width 2.9 --out before
python render.py --preview-bars 48 --out after
python review_score.py after/Blue_Hour_Signal.score.json --strict
python check.py after --preview
```

Control tempo, transpose and reproducible performance seed with `--bpm`, `--transpose`, and `--seed`. Control stereo with `--stereo-width` (0.75–3.10, 1.95 default). `--no-development` deliberately disables phrase variation to facilitate controlled A/B comparisons.

## What's verified and what is not

Automated tests cover chord spelling, melodic identity, variation, deterministic repeatability, score schema, MIDI, synthesizer pitch, drum variation, decoding and DSP integrity. Repeated verse/chorus phrase ratios are measurably lower without removing the main hook; this is not a claim that the new version is preferred by listeners. A green QA report is a technical acceptance gate, **not a musical taste evaluator**.

Research rationale and next experiments: [docs/v4-findings.md](docs/v4-findings.md).
