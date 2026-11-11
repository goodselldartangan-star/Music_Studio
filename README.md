# Music Studio v3 — Blue Hour Signal

A fully original 3:34 instrumental at 118 BPM: indie-pop plucked guitar meets pulsing electronic drums, atmospheric keys, and a melodic synth hook. Built by ChatGPT using offline deterministic Python synthesis. **No external AI services, APIs, logins, reference audio, soundfont downloads, or required user input.** The three provided recordings were used only for high-level analysis of dynamics, stereo placement, and tonal balance, not copied.

## One command per stage

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python render.py --preview-bars 8 --out preview
python check.py preview --preview
python render.py --out output
python check.py output
```

Files: `output/Blue_Hour_Signal.mp3` (320 kbps), `Blue_Hour_Signal.wav` (24-bit), `Blue_Hour_Signal.mid`, `Blue_Hour_Signal.score.json`, `qa_report.json`. `ffmpeg` and `ffprobe` must be installed.

## Replaceable pieces

| File | Single responsibility | May import |
|---|---|---|
| `studio3/spec.py` | Stable Settings/Note/Drum contracts, timeline | Python standard library |
| `studio3/composition.py` | Songwriting and arrangement into portable JSON score | `spec`, NumPy |
| `studio3/instruments.py` | Individual sounds (`Note` or percussion -> mono float32) | `spec`, NumPy, SciPy |
| `studio3/midi.py` | Convert score into MIDI | `mido` |
| `studio3/mix.py` | Position voices, mix separate buses, effects and write WAV | `spec`, `instruments`, NumPy, SciPy, soundfile |
| `studio3/quality.py` | Independent, **non-AI** media acceptance checks | `spec`, ffmpeg/ffprobe, NumPy, SciPy, soundfile, mido |
| `render.py`, `check.py` | Tiny CLI façades | corresponding modules |

Dependency direction is one-way. A new guitar sound requires only `instruments.py`; a new chord progression only `composition.py`; EQ or loudness changes only `mix.py`. Avoid modifying the shared score format unless versioning it. Other code (`studio_v2.py`, `offline_song.py`) remains intact for comparisons.

## Tune without rewriting

```bash
python render.py --bpm 105 --transpose=-2 --seed 876 --preview-bars 32 --out alternate
python check.py alternate --preview
```

For full-song export, omit `--preview-bars`. Seed controls deterministic timing/velocity/excitation; transpose is constrained to ±5 semitones. Every test should run before a complete render, and QA should run before release upload.

## Research and observed improvement

At selected 12-second excerpts, the earlier v2 mix had high stereo correlations around 0.986, whereas the reference recordings ranged roughly 0.73–0.93 in similar sections. Stereo bass is now mono-compatible below 145 Hz while musical side information above that is widened; the new mix's first 28 seconds measure 0.868 correlation. Loudness is −14.0 LUFS, loudness range 11.6 LU, WAV true peak −1.7 dBTP and decoded MP3 true peak −1.5 dBTP. These are **technical comparisons**, not proof of musical resemblance or subjective quality.

## Originality, licensing and limitations

Original composition, instrumentation and algorithms, influenced by broadly taught physical-model synthesis and audio-production ideas. Uses existing NumPy, SciPy, SoundFile, Mido and FFmpeg libraries under their own licenses; does not copy audio clips, melodies or code from the reference recordings. See `docs/v3-notes.md` for comparison and research sources. Listening and musical taste remain personal; a passing signal test does not establish that a listener will enjoy the result.
