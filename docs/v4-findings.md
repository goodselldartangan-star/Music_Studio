# Music Studio v4 — what helps GPT compose better music

**Design constraint:** GPT writes the arrangements and the code; local deterministic DSP renders audio. No other generative-AI model, paid account, API key, audio model or new user input is required.

## Evidence-informed reasoning

- *LLMs can read music, but struggle to hear it* (PMLR 2026): the tested models are much better at MIDI/symbolic tasks than parallel audio-perception tasks, and prompting alone offers limited improvements. Our response: provide symbolic scores and deterministic checks rather than claiming the assistant can listen like a person. https://proceedings.mlr.press/v303/carone26a.html
- *Whole-Song Hierarchical Generation of Symbolic Music Using Cascaded Diffusion Models* (ICLR 2024) studies form → phrase → local note hierarchy. We borrow the **architecture principle**, not the diffusion model or another AI. Our score stores sections, chords and events; `development.py` edits later phrases while preserving the main hook. https://proceedings.iclr.cc/paper_files/paper/2024/hash/39d239a30bb40536a5e4e78b5780ba82-Abstract-Conference.html
- *Aligning Text-to-Music Evaluation with Human Preferences* (ISMIR 2025) finds many objective audio metrics poorly aligned with perceived musical quality. Therefore our audits are **guards**, not goodness scores; musical decisions remain revisable. https://zenodo.org/records/17811347
- `music21` supports richer chord/voice-leading analysis if the system grows; it is not yet required. Our six-chord vocabulary is checked with 50 lines of stdlib Python instead, reducing complexity. https://music21.org/music21docs/moduleReference/moduleVoiceLeading.html

## Actual changes

1. `studio3/theory.py`: names must match the sounding voicings. Relabelled Gmaj7 → Gmaj9 and A6sus → A6/9, and corrected F#7sus to a true F#7sus4 without its major third. These labels now match exact pitch-class sets.
2. `studio3/development.py`: pure immutable-score transform. Verse 2 varies its answers instead of cloning verse 1; last chorus retains identifiable opening gestures but varies subsequent rhythms and resolutions. Off-key legacy notes are flagged and adjusted by one semitone where possible.
3. `studio3/review.py`: lightweight report of phrase copying, melodic leaps, scale vocabulary, and chord naming. `review_score.py` exposes this without rendering. The new render defaults to developed score; `--no-development` provides old arrangement for A/B testing.
4. `studio3/mix.py`: stereo width is a parameter stored in the score instead of magic-number amplification, and can be changed without touching instruments.
5. `studio3/quality.py`: rejects a developed full master whose symbolic audit fails, in addition to its existing sample/MP3/loudness tests.

## Measured symbolic difference, same song

In the baseline score, 11/16 verse pairs and 12/16 chorus pairs are **exact** lead-note matches by relative beat, pitch and duration. After the development transform, they are 0/16 and 4/16 respectively. Original recognizable downbeat hook phrases at bars 32, 40, 80 and 88 remain identical. This does **not** measure melodic beauty; it detects one fixable source of rote repetition.

## GPT editing loop (no extra AI)

1. Plan form and harmony before notes (intent, section length, tension/release, recurring hook).
2. Change one short passage in composition/development modules; avoid editing the rendering or output schema to alter a melody.
3. Generate and inspect portable score + `composition_review.json`; reject bad chord voicings, off-key accidents, overly identical answers.
4. Render 8–16-bar A/B clips with identical instrument settings and matched loudness. Listen if a real listening capability is available; otherwise report measurements without making subjective claims.
5. Once the excerpt passes, render the full track and run `check.py` for decoded MP3, WAV/MIDI, section energy, stereo and true peak.
6. Only publish masters after tests. Preserve the baseline for rollback.

## Next experiments

- Test candidate melody variants with phrase-contour similarity, cadence placement and instrumentation contrasts rather than optimizing a single scalar score.
- Study timbre and room realism, but only adopt sample packs/soundfonts after checking licenses and actual sound quality.
- If human listening preferences are available later, use blind A/B listening at matched loudness; never infer popularity from technical checks.
