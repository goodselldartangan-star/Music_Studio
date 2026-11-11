# Music Studio — sound realism and GPT-6 audit (2026-11-11)

**Purpose:** The user has rejected the quality of the radio-style instrumental. Do not treat successful encodes, LUFS, stereo width or unit-test counts as evidence that it sounds good. GPT is the only AI allowed; ordinary code, DSP, sampled instruments and open-source audio tools are allowed. No API keys or mandatory user input.

## Observed shortcomings

Inspection of the last project's `radio_composition.py`, `radio_instruments.py`, and `radio_mix.py`:

- A functioning MIDI/score sequencer and simplified synthesizer is not the same as a believable indie-pop/electronic production. The pluck is a simple Karplus–Strong instrument, lead notes use a few oscillators, and drum waveforms use modeled noise and oscillators. More volume, widening and filtering will not substitute for recorded attacks, articulations, damping and resonances.
- The 96-bar, 118-BPM song repeats four-bar harmony and accompaniment templates; the lead hook returns with small algorithmic edits.
- In the rendered score, the main lead's median chorus note lasts approximately **0.29 seconds** and no lead note lasts 1.0 second. A vocal-like topline needs more dynamic phrasing and genuine pauses, although no universal note-length target defines a good melody.
- Note counts are high: **560 arp / 524 plucks / 381 bass / 274 lead / 1,577 percussion events**. Dense accompaniment can bury a hook even with clean mixing.

## A measured comparison, not proof of musical similarity

For 55–85 seconds of the generated song and three supplied reference recordings, decoded at stereo 22.05 kHz: stereo correlation was **0.929** for `Headlights on the Water`; approximately **0.833, 0.800, 0.608** for the three reference excerpts. The references contain singing, so the comparison is not apples-to-apples and cannot serve as a hard threshold. Raw power in 3–10kHz was 2.7% for Headlights and 3.7%, 2.5%, 1.4% for the references. This spread illustrates why spectral-target optimization alone is inadequate.

## What to research / prototype before another full song

1. **Sound authenticity:** keep an oscillator fallback but add a sample/soundfont backend behind the existing mono note waveform interface. Test license-verified **CC0** Karoryfer guitar/bass/drums or VSCO 2 Community samples and an optional **CC BY 3.0** Salamander piano with attribution. Use actual velocity layers and deterministic round-robin where available. Sampling is not another AI.
2. **Compose the hook first:** GPT proposes 3 distinct 2–4-bar melodies with rests, longer phrases and call-and-response. Validate chord relationships, render each over identical accompaniment, and compare at matched loudness.
3. **Arrangement restraint:** compare the same 12–16 seconds with arp removed, kick/bass simplified, and one deliberate pre-chorus break. Do not confuse more notes with emotional lift.
4. **QA:** report stems separately, detect clipping, phase problems, excessive masking and unexpected silence. Use metrics as guardrails, never as claims of human aesthetic approval.
5. **Independent modules:** preserve stable score and note/drum contracts; `composition` -> `score` -> `instrument backend` -> `stems/mix` -> `QA`. Keep current generator for fallback and reproducibility.
6. **Test small, then integrate:** render 8–16-second loudness-matched A/B clips with identical MIDI before touching whole-song arrangement. If no actual human-style audition occurs, report that limitation rather than claiming good sound.

## Why GPT-6 alone doesn't fix this

GPT-6 is valuable for music form, counterpoint ideas, constrained score drafting, writing and refactoring DSP code, reading reports, and designing controlled experiments. It does **not** transform the current simplified synthesizer into a recording studio, nor can it update its own model weights. The API's GPT-6 model specifications describe text and image capabilities, not a dedicated controlled music-waveform output. Research finds LLMs perform better on symbolic music than audio perception, and automated music metrics disagree with listener preference. Better prompts or longer reasoning are not substitutes for audio instruments and listening feedback.

## Sources

- Carone et al. (PMLR 2026), audio vs symbolic music perception: https://proceedings.mlr.press/v303/carone26a.html
- Music evaluation and human preferences: https://arxiv.org/abs/2506.19085
- Berklee hook writing through contrast, placement, repetition: https://online.berklee.edu/takenote/how-to-write-songs-with-killer-hooks/
- CMU computer music sampling vs modeling: https://www.cs.cmu.edu/~15322/book/ch11/02.html
- Velocity layers and round-robin realism: https://www.soundonsound.com/techniques/how-virtual-instruments-work
- Karoryfer CC0 samples: https://shop.karoryfer.com/pages/free-samples
- Versilian VSCO 2 Community (CC0): https://versilian-studios.com/vsco-community/
- Salamander Grand Piano (CC BY 3.0): https://sfzinstruments.github.io/pianos/salamander/
- SFZ engine sfizz: https://github.com/sfztools/sfizz
- GPT-6 model documentation: https://developers.openai.com/api/docs/models

**Status:** diagnosis only. No new song has passed a listening-based acceptance test. Preserve this note for future work; do not claim further progress based on research alone.
