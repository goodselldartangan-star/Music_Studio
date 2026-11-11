# Music Studio — offline music creation (v2)

A self-contained original instrumental studio. **ChatGPT is the only AI involved:** the render program itself is deterministic Python DSP, with no external generative AI, no music APIs, no paid subscription, no download of sound samples, and no extra user input.

## New track: Porchlight Receiver

- **3:09 • 114 BPM • 88 bars** • alternative electronic / indie-pop instrumental.
- Original instrumental hook, syncopated bass, physically modeled plucked strings, layered synthesis, drum groove, arpeggios, section-by-section dynamics and contrast.
- 2,432 pitched notes, 1,235 programmed drum hits, 24-bit WAV / 320 kbps MP3 / MIDI / full JSON score.
- The engine is `studio_v2.py`; audio acceptance tests are in `quality_v2.py`. These must pass **before** the release workflow publishes anything.

## Run it locally — no API keys

Requires Python 3.10+, FFmpeg/FFprobe, and the small set of Python libraries in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python studio_v2.py --out output_v2
python quality_v2.py output_v2
```

The completed MP3 is `output_v2/Porchlight_Receiver.mp3` and the lossless 24-bit stereo WAV is in the same folder. The program creates an editable `.mid` and `.score.json` too. The [GitHub workflow](.github/workflows/render-song.yml) runs tests and uploads/publishes only passing audio.

### Test new arrangements before a full render

```bash
# Fast preview before recording the full song
python studio_v2.py --preview-bars 8 --out preview
python quality_v2.py preview --preview

# Optional tempo/key/performance controls; no outside AI
python studio_v2.py --bpm 103 --transpose -3 --seed 4321 \
  --preview-bars 8 --out preview_alt
python quality_v2.py preview_alt --preview

# Score and MIDI only
python studio_v2.py --score-only --out score_only
```

`--bpm` accepts 90–145, `--transpose` accepts -5 to +5 semitones, and `--seed` produces repeatable groove variations. Melody, chord selection and section structure remain original authored ideas; configuration is not a claim that entirely new compositions are generated on demand.

## What improved over the previous version?

- Plucked instruments now use an original Karplus–Strong/digital-waveguide family model, not only combinations of fixed harmonics.
- Percussion and plucks vary accents and microtiming by a deterministic seed; kick and strong backbeats stay aligned.
- Lead notes have independent articulation and evolving vibrato, not just identical attack/release every time.
- Separate drums, bass, plucks, keys and melody buses replace a single whole-mix presence boost.
- High-frequency nonlinear saturation is run at 2× sample rate before resampling back to reduce aliasing.
- QA now measures integrated loudness, loudness range, estimated true peak, stereo balance, MP3 decoding and section dynamics.

See [research and measured results](docs/v2-research.md). **Passing engineering tests is not equivalent to human listening or musical taste.**

## Previous work

`offline_song.py` still reconstructs *Streetlight Letters*. `afterglow_atlas.py` and `test_audio.py` preserve the first offline instrumental experiment. `music_studio.py` and its example plan document an older optional external-provider approach; the v2 workflow **does not call it or require any API credentials**. Prior songs, releases and history are preserved; new v2 audio is a separate release. None of the user's reference recordings is committed.