# Music Studio — Afterglow Atlas

An original **melodic electronic / cinematic instrumental**, written as a deterministic 72-bar arrangement and rendered locally with Python DSP. No samples from copyrighted songs, no paid API, and no external audio assets are required.

## The song
- **Title:** Afterglow Atlas
- **Tempo:** 116 BPM · **Meter:** 4/4 · **Duration:** ~2:34
- **Harmonic center:** D minor, turning toward F major
- **Instruments:** warm synth bass, atmospheric pads, felt-style piano, plucked arpeggios, lead synth, bells, and programmed electronic drums
- **Form:** intro (8 bars), verse (16), build (8), chorus (16), breakdown (8), final chorus (12), outro (4)
- **Main motif:** A–C–D–F, answered by E–D–C–A, developed through several sections

The [GitHub Actions audio build](.github/workflows/render-song.yml) renders and tests the complete song and provides MP3, 24-bit WAV, MIDI and machine-readable score artifacts. Download the permanent [Afterglow Atlas release](https://github.com/goodselldartangan-star/Music_Studio/releases/tag/afterglow-atlas-v1) (MP3, WAV, MIDI and score), or get the artifact from the latest successful **Render original song** workflow run.

## Rebuild locally

1. Clone this repository. The [editable renderer](afterglow_atlas.py) and [audio tests](test_audio.py) are directly in the repository root. The [source ZIP](source/Music_Studio_Source.zip) contains an exact tested snapshot as well.
2. Install `python -m pip install -r requirements.txt`.
3. Render with `python afterglow_atlas.py --out output`.
4. Run checks with `python test_audio.py`.
5. Make the listening MP3 with `ffmpeg -y -i output/Afterglow_Atlas.wav -codec:a libmp3lame -b:a 320k output/Afterglow_Atlas.mp3`.

The source archive includes matching `afterglow_atlas.py` and `test_audio.py` copies used by the successful GitHub Actions build. Regeneration does not require GitHub Actions or any AI music generation subscription.

## Quality checks

The test suite checks exact duration, playable stereo PCM and MIDI, finite samples, digital peak below the clipping threshold, consistent song sections, stronger choruses than verses and breakdown, left/right balance, healthy stereo correlation, and bounded subsonic and ultra-high-frequency energy. These are objective audio-engineering checks, **not a substitute for human critical listening**.

Composition techniques followed: plan song form, use a concise identifiable motif, repeat and vary it, choose chord colors intentionally, build tension and release, and contrast sparse and full passages. Inspired by the songwriting-education principles published by Berklee Online, without copying any particular composition.

**Authorship:** created for this Music Studio repository in November 2026. All composition and synthesis code are original.