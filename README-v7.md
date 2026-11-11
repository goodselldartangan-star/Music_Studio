# Music Studio v7 — instrument fit and musical effects

Three new ~35–41-second original instrumental listening sketches with independently authored arrangements. **No other generative AI, keys, or required user input.** V6 remains untouched; v7 lives in small interchangeable modules.

| Module | Responsibility |
|---|---|
| `studio7/score.py` | Arrangement, instrument roles and note lists |
| `studio7/audit.py` | Music-theory and performance compatibility checks |
| `studio7/samples.py` | Optional CC0 nylon-guitar recorded sample reader |
| `studio7/render.py` | Recorded backend selection, stem gain and mix routing |
| `studio7/effects.py` | Standalone DSP: room, delay, tremolo, chorus, sidechain, saturation |
| `studio7/qa.py` | Independent MP3/QA checks |
| `demo_v7.py` | Small CLI, no DSP internals |

`studio6/soundfonts.py`, `studio3/sample_bank.py` and the existing sample installers are reused without source changes. This prevents changes in the sampler from rewriting the score.

## Run offline

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_studio7.py' -v
# Portable fallback demos, GM sample bank installed on system:
python demo_v7.py --gm /usr/share/sounds/sf2/TimGM6mb.sf2 --out local-v7
# Download higher-quality recorded instruments in the GitHub workflow,
# then use their local installation:
python demo_v7.py --assets assets/v7 --out recorded-v7
```

The recorded audio is produced on GitHub Actions through `.github/workflows/music-studio-v7.yml`, which downloads samples from the original creators and publishes verification reports. No samples or reference MP3s are checked into the repository. See [research and precise fixes](docs/engine_audit_v7.md).
