# Q4 — Piano pedal and continuous-note realism: research and first isolated timing layer

**Scope:** decide what Music Studio's actual piano sample assets can model, and what new licensed assets/sampler support would be needed before claiming realistic pedaling. Earlier OGG, stereo WAV, strings and MP3s remain unchanged.

## Source findings

- Music Studio's Meta upright piano collection has 88 keys × 4 note-on velocity layers = **352 recorded notes**. The verified filenames and supplied SFZ map are not a standalone set of recorded pedal-down, hammer-key-release or sympathetic-resonance layers. The existing `smooth_release` envelope handles a normal sample note-off, not physical pedal behavior. [Publisher Meta Piano design](https://github.com/facebookincubator/Meta-open-sound/blob/main/systems/instruments/meta-piano/README.md).
- The **Salamander Grand Piano V3**, author Alexander Holm, is an independent [CC BY 3.0](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/master/README.md) instrument. It advertises **16 velocity layers**, sampled key releases, string resonances and separate pedal-up/down mechanical noises. The [actual SFZ](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/master/Salamander%20Grand%20Piano%20V3.sfz) includes `trigger=release`, `note_polyphony=1`, `off_time=0.5`, and CC controls (pedal CC64, string resonance CC20, hammer CC21, pedal noises CC22). The [pedal regions](https://github.com/sfzinstruments/SalamanderGrandPiano/blob/master/Data/pedal.txt) separately play up/down noises.
- **Compatibility blocker:** the current Music Studio offline adapter (`studio6/soundfonts.py`) uses **FluidSynth SF2**, not an SFZ/ARIA sampler. The Salamander SFZ authors explicitly warn that ARIA extensions are needed for full function. Its note-selfmasking can limit older same-pitch voices depending on velocity (see [SFZ note_polyphony semantics](https://sfzformat.com/opcodes/note_polyphony/)), so the user's independent long-note/short-repluck requirement must be demonstrated before accepting any new backend.
- Stereo/source-quality improvement and true pedal response are **different questions**. Q3 verifies stereo masters; Q4 must separately test event scheduling, release sample playback and sympathy resonance.

## Q4 first component — basic note-off deferral only

`studio7/pedal_timing.py` adds `apply_piano_pedal_windows(score, windows)` as a pure score-copy transformation. Windows represent a simplified **CC64 pedal-down/up interval**, and only piano key-offs that would occur while the pedal is held are extended to the specified pedal-up beat. Velocity, pitch and attacks are unchanged. Explicit repeated same-pitch notes remain independent voices; a pedal-down cannot become a stuck note after the score ends. This is **not** sampled pedal mechanism or sympathetic resonance.

The authored opt-in `--piano-pedal-timing` is limited to the 16-bar **Silver** sketch: its intro remains dry and build/final sections re-pedal briefly before each chord change. This is a controlled expression experiment, **not a musical recommendation for all songs**. Defaults and released audio remain identical.

## Acceptance checks

- [ ] Five focused score tests including overlapping same-pitch notes, valid pedal-up, unchanged intro/nonpiano parts and invalid/unterminated window rejection.
- [ ] Dedicated offline GM piano A/B and full Silver MP3 QA.
- [ ] Full recorded Meta CC0 piano integration and no-overwrite release checks.
- [ ] Later, if a sampler capable of ARIA extensions and genuine released samples is available, isolated test for CC64, hammer/release/sympathetic layers and repeated-note behavior. No source library adoption before tests.

**Boundary:** Pedal note-off deferral is one real aspect of keyboard control; it does not make ordinary note-on samples reproduce a real piano soundboard or dampers. Even a verified larger library would need an acoustic listening choice before claiming superior musical realism.
