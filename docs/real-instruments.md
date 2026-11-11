# Music Studio recorded instruments (optional offline backend)

## Why this exists

GPT composes MIDI, but sine-based sounds are not the same as real piano or guitar performances. This drop-in replacement lets a v4 score render recorded notes without changing composition or MIDI export. It is an ordinary sampler, **not another AI service**.

The default synthesizer remains unchanged. Passing `--sample-root` selects recorded samples for `pluck` (steel-string guitar) and `keys` (upright piano). Bass, pads, synth melody and drums continue through the original engine; place optional licensed drum WAVs in `assets/cc0-samples/drums/kick/`, `snare/`, `hat/`, etc. if available. A sampled note uses nearest pitch within four semitones, dynamic layer selection, predictable alternate-sample selection, resampling, and note-off release. `--require-samples` fails if either of the two main packs is missing.

## Verified publisher, files, licenses

**Meta Open Sound**: https://github.com/facebookincubator/Meta-open-sound — produced by Meta's Creative Audio team. Its three instruments are licensed **CC0 1.0 Universal**; they can be used, edited and redistributed without attribution. The *separate* Oculus sound-effects collection is **CC BY 4.0**, so do not combine it without retaining attribution.

- **Steel-string guitar, 375 recordings, 3 velocity layers** (25,440,465-byte compressed OGG pack): https://github.com/facebookincubator/Meta-open-sound/releases/download/meta-steel-guitar-v1.0.0/meta-open-sound-meta-steel-guitar-ogg.zip
- **Piano, 352 recordings, 4 velocity layers** (48,182,243-byte compressed OGG pack): https://github.com/facebookincubator/Meta-open-sound/releases/download/meta-piano-v1.0.0/meta-open-sound-meta-piano-ogg.zip
- **Nylon guitar, 348 recordings, 3 layers**, optional future source (16,483,193-byte pack): https://github.com/facebookincubator/Meta-open-sound/releases/download/meta-nylon-guitar-v1.0.0/meta-open-sound-meta-nylon-guitar-ogg.zip

The WAV masters are hundreds of MB and unnecessary for initial tests; these OGGs are lighter and loadable by libsndfile. **No upstream samples are checked into this project.** Each install records source, release asset and downloaded ZIP SHA256 under `assets/cc0-samples/provenance.json`.

### Automatic installation (GitHub Actions)

On a change to the sampler, `.github/workflows/recorded-instrument-preview.yml` obtains the two OGG release files using `gh release download` on GitHub's runner, verifies the ZIP structure and runs a strict sampled-vs-synth A/B preview test. No personal account, API key or user download is needed. It stores the resulting WAV previews and comparisons as temporary workflow artifacts, not repository files. The default song renderer is not replaced until the first real-sample A/B build passes.

### Install locally

```bash
python tools/install_cc0.py --out assets/cc0-samples
python -m unittest discover -s tests -v
python render.py --preview-bars 8 --sample-root assets/cc0-samples --require-samples --no-mp3 --out previews/sampled
python tools/compare_previews.py previews/synth/Blue_Hour_Signal.wav previews/sampled/Blue_Hour_Signal.wav --out previews/AB.wav
```

If local download access is blocked, use the two direct publisher links above, then:

```bash
python tools/install_cc0.py --no-download --guitar-zip ~/Downloads/meta-open-sound-meta-steel-guitar-ogg.zip --piano-zip ~/Downloads/meta-open-sound-meta-piano-ogg.zip --out assets/cc0-samples
```

The exact filenames are meaningful; do not rename individual notes after extraction.

## Audio-engineering and research limitations

- A recorded note doesn't automatically produce a realistic guitar performance. Actual string choices, pick directions, muting, breath-length phrases, articulations, and rhythmic phrasing will need composition and engine work.
- Synthetic kick/snare/hi-hat remain. An acoustic kit could be integrated after verifying a good CC0 library. FreePats' 2020 Muldjord acoustic kit is **CC BY 4.0** and significantly larger (~157 MiB FLAC); keep attribution if used: https://freepats.zenvoid.org/Percussion/acoustic-drum-kit.html
- A/B testing must compare at similar listening loudness, since louder often seems better. Tests establish no clipping, valid decoding, use of real files, and differences in texture; listener preference cannot be inferred automatically.
- Local production environments may be network-isolated. The GitHub Actions setup is intended as a second self-service route; until that CI succeeds, only the synthetic-fixture tests are verified.
