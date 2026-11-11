# Headlights on the Water — Original instrumental radio-pop single

**3:18 · 118 BPM · 96 bars · F# minor / A major.** Entirely original instrumental music, with a guitar-like plucked rhythm, synth-bass groove, electronic/indie drums, and an expressive instrumental melody in place of vocals.

The independent `studio3/radio_composition.py` songbook generates a portable score. The synthesizer, MIDI export, mixer, and checker are separate modules. No external generative AI, keys, credentials, copyrighted samples, or uploaded reference recordings are used.

## Rebuild

Requirements: Python 3.10+, NumPy, SciPy, SoundFile, Mido, FFmpeg and FFprobe.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python render_radio.py --score-only --out score_only
python render_radio.py --preview-bars 36 --out preview
python render_radio.py --out output
```

On success, `output/Headlights_on_the_Water.mp3` is the 320 kbps master, alongside stereo 24-bit WAV, MIDI, a JSON note/drum score, composition preflight and objective audio-quality report.

## Structure

| Section | Bar range | Purpose |
|---|---|---|
| Intro | 0–3 | Establish the guitar rhythm and teaser hook in under 10 seconds |
| Verse 1 | 4–15 | Sparse melodic phrasing and bass/guitar groove |
| Prechorus | 16–23 | Rising melodic phrase, rhythmic build |
| Chorus 1 | 24–35 | Singable instrumental hook (arrives about 49 sec) |
| Postchorus | 36–39 | Brief hook echo |
| Verse 2 | 40–51 | New replies and rests |
| Prechorus 2 | 52–59 | Stronger build |
| Chorus 2 | 60–71 | Recognizable hook, changed phrase endings |
| Bridge | 72–79 | Dynamic contrast, changed harmonic shape |
| Final chorus | 80–91 | New harmonic counterline, stronger arrangement |
| Outro | 92–95 | Resolved ending with a soft tail |

## Module boundaries

- `studio3/radio_composition.py`: song form, harmony, hooks, bass lines and percussion score
- `studio3/radio_instruments.py`: replaceable timbres; reuses physical-model plucks
- `studio3/radio_mix.py`: separate bus processing, stereo effects, 2× oversampled saturation and final WAV
- `studio3/midi.py`: MIDI export (unchanged contract)
- `studio3/radio_quality.py`: composition tests, audio file integrity, stereo, LUFS, LRA, and WAV/MP3 true peak
- `render_radio.py`: thin orchestration, score → synth → export → gate

This code is isolated from the main studio engine, so future changes cannot break previous song versions. The project is deterministic with fixed `--seed` and `--bpm` arguments.

## Reference analysis and limits

Three user-supplied songs were analyzed locally for broad traits only: verse/chorus balance, loudness range, stereo spread, and general bass/treble distribution. No source samples, notes, lyrics, or recordings were copied into this project.

The master passed objective technical checks: −14.4 LUFS, 9.5 LU LRA, −1.5 dBTP on decoded MP3, and a strong final-chorus contrast. Audio-engineering checks cannot establish radio success or listener preference, nor substitute for human critical listening. Research includes Berklee Online's [Songwriting Handbook](https://assets.online.berklee.edu/handbooks/berklee-online-songwriting-handbook.pdf) and the AES [true peak explainer](https://aes.org/resources/audio-topics/loudness-project/learn-more/).
