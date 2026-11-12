# P7 — Mix translation, low-end mono and stem spectral inventory

**Scope:** technical cross-device checks. No musical note, sample, gain target, instrument part, reverb setting or original master is rewritten.

## Initial measured issue

The existing two-pole `mono_below` reduced the width of low frequencies but allowed some phase-shifted side residue. A strict low-frequency mono test in P6 uncovered this difference. The P7 approach adds an **optional**, stronger filter of the stereo side channel below the crossover while leaving the center `(L+R)/2` waveform untouched.

New `studio7/mix_translation.py::precise_mono_below` uses a fourth-order high-pass applied forward/backward to the stereo **side** signal. This is an offline zero-phase option; it is deliberately not enabled by default because it can change stereo feel and transients. Command line: `demo_v7.py --precise-low-mono`, with distinct `-p7-mono` output suffix.

## Objective measurements and tests

[Successful focused P7 workflow 43151612573](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43151612573) passed **31 tests**, same-score/same-sample mix before/after, MP3 decode and a complete After arrangement render.

In the measured 16-second section of an After GM mix:

| Technical metric | Original crossover | Optional precise crossover |
|---|---:|---:|
| Low-band stereo side fraction | 0.000054 | 0.000012 |
| Absolute low-band side RMS | -69.193 dBFS | -75.842 dBFS |
| Estimated 4× interpolated true peak | -3.641 dBFS | -3.641 dBFS |

The low-side level is **already low** in the original. The reduction is technically real but may be inaudible in this arrangement. A fully anti-phase isolated signal has no mid energy, so its *relative side fraction* remains 1.0 even when its absolute side energy is suppressed: the audit now explicitly measures absolute low-band dBFS to avoid this error.

Additional `tools.audit_mix_stems_p7` provides independent per-stem RMS and spectral occupancy in 35–160, 160–500, 500–2000 and 2000–8000 Hz. This is an inventory to guide later arrangement/EQ decisions, **not** a masking or aesthetic score.

## Remaining gates

- [Expanded P7 same-patch run 43151836846](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43151836846): **passed 33 tests**, added the processed-stem inventory, full before/after mix and MP3 decode.
- [Full real recorded-instrument run 43151867062](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43151867062): **passed** all base sample renders plus the optional After P7 mono-filter render and MP3 QA.

## Limitations

True-peak here is an oversampled PCM **estimate**, not an international mastering standard certification. RMS/phase/spectral-band measurements do not establish desirable subjective EQ, musical masking or better playback on all devices. Perceived mix decisions should remain separate from technical defect prevention; do not tune a master to an arbitrary target curve without reference and listening context.

## Processed stem inventory (After GM fixture)

- **Drums:** -23.8 dBFS RMS; 84.86% of measured 35–8000 Hz energy in 35–160 Hz.
- **Bass:** -24.46 dBFS RMS; 40.93% in 35–160 Hz and 54.16% in 160–500 Hz.
- **Electric guitar:** -27.87 dBFS RMS; 57.15% in 2000–8000 Hz.
- **Lead:** -22.86 dBFS RMS; 82.83% in 500–2000 Hz.

This describes different spectral *roles* and possible low-band kick/bass overlap, not actual listener masking. **P7 engineering gate accepted**; any choice to rebalance EQ/levels remains musical-context work rather than a mandatory numerical target.
