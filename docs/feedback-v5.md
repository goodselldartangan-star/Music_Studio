# Music Studio v5 — Real drum samples, phrasing and mix comparisons

This is a small enhancement, **not a rewrite**. There is no additional AI system, API key, external production service, or requirement for user participation to generate music. The existing score JSON and MIDI interfaces are unchanged.

## Replaceable components

- `studio3/performance.py`: deterministic score transforms. Adds melodic breath gaps and phrase-ending holds, bass aligned with near-downbeat kicks, and drum groove performance profiles. No sound engine dependency.
- `studio3/sample_bank.py`: reads pre-existing recorded samples, now with snare ghost-note handling and differentiated drum gains; keeps oscillator fallback.
- `studio3/mix.py`: audio render now understands per-example bus gains, can insist on recorded percussion, and chokes sampled open hats at the next closed hat.
- `tools/install_cc0_drums.py`: downloads exactly 11 allowlisted CC0 drum WAV files from [Boochi44/free-drum-samples](https://github.com/Boochi44/free-drum-samples). Each file is checked by its pinned Git blob hash. Files go into ignored `assets/cc0-samples/drums`, never Git source history.
- `tools/render_feedback.py`: 3 independent, contrasting 12-bar MIDI/WAV/MP3 mini-arrangements.
- `tools/verify_demos.py`: verifies decoded MP3, finite WAV audio, duration, peaks, balance, distinctness and actual recorded-note/drum usage. **It cannot rank their subjective appeal.**

The two CC0 recorded guitar/piano instruments are obtained from [Meta Open Sound](https://github.com/facebookincubator/Meta-open-sound); see `docs/real-instruments.md`. Guitar and piano sample ZIP files are not included in the source repository. All downloads occur during GitHub Actions workflow run, pinned by hashes.

## The three 27–29 second examples

1. **Indie** — guitar-led, restrained drums, snare slightly behind the beat, a rising pre-chorus and first hook.
2. **Electro** — brighter electronic pop, locked kick-and-bass pulse, keys/lead forward, strong repeated hook.
3. **Hybrid** — wider atmospheric bridge, fewer high hats early, spacious arrangement followed by a fuller chorus.

This is intended for *direct user feedback*, not an automatic winner selection. The examples deliberately contrast composition and instrumentation, and inherit the original song's recognizable hook; they do not borrow audio or melodies from the user's recordings.

## Run

```sh
python -m unittest discover -s tests -v
python tools/install_cc0_drums.py --out assets/cc0-samples
python -m tools.render_feedback --sample-root assets/cc0-samples --out feedback-examples
python -m tools.verify_demos feedback-examples
```

To use the recorded guitar and piano too, run `python tools/install_cc0.py --out assets/cc0-samples` before rendering. `--require-drums` and `--require-samples` will fail closed if libraries are absent. The GitHub Actions workflow downloads all sources itself and tests that actual recorded notes are played before publishing.

**Research basis:** velocity layers, round-robin sampling, meaningful note separation, hat choke groups, disciplined instrument interaction, and A/B at comparable listening levels. Every track has an independently editable score; user feedback should guide subsequent artistic decisions.
