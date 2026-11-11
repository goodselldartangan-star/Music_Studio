# P3 rhythm section — baseline audit and first optional pocket experiment

**2026-11-11 · P3 still active.** This report distinguishes technical timing relationships from musical groove preference. No original v7 note/drum source was overwritten, and nothing in the default rendering path changed.

## Why investigate

All three existing scores deliberately place some bass note entrances *after* their nearest downbeat kick, but those delays are larger than the modest "laid-back" timing offsets used in many pop/rock arrangements. This does not prove an error. Across styles and songs, kick and bass can deliberately coincide, push, drag, or interleave; imposing one universal quantize setting could flatten the feel.

Music-production sources:
- [Sound on Sound: Kick and bass mix tips](https://www.soundonsound.com/techniques/mix-tips-kick-bass)
- [Ableton Manual: separate timing, quantize and velocity groove controls](https://www.ableton.com/en/manual/using-grooves/)
- [Producer Tips: ahead/behind kick creates distinctly different bass groove](https://www.macprovideo.com/article/Synth-Sound-Design/producer-tips-creating-basslines-for-beginners)

## Score-only baseline (no changes)

`python -m tools.audit_rhythm_p3` measures kick, bass, snare and hats independently. A 40ms flag is a *review threshold*, not an absolute rule.

| Original score | Median downbeat bass lag after kick | Anchors beyond 40ms | Median snare lag from beat | Hat timing median vs half-beat |
|---|---:|---:|---:|---:|
| Harbor | 61.11 ms | 12 | 10.00 ms | 0.00 ms |
| After | 63.93 ms | 16 | 6.39 ms | 0.00 ms |
| Silver | 94.12 ms | 8 | 14.71 ms | -5.88 ms |

The audit preserves bass pickups and silence without kick; intros are not incorrectly flagged as missing drum timing. The [read-only baseline workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43118680421) passed its tests and stored machine-readable results as a GitHub artifact.

## Controlled P3 option

The new, **opt-in** `studio7/rhythm.py::shape_pocket` works exclusively on bass notes that clearly function as kick-associated downbeat anchors. It never moves kick, snare, hat or offbeat pickup events, never transposes or adjusts velocity, and skips changes that would crowd a preceding bass note's release. Its target behind-kick offsets are separate per style: Harbor 23 ms, After 17 ms, Silver 38 ms.

- `demo_v7.py --rhythm-pocket` produces a separate `-p3-pocket` recording without overwriting originals.
- All five `tests/test_rhythm_pocket_p3.py` tests protect pickup timing, intro bass without kick, overlapping previous releases, deterministic results, and the existing score/harmony review.
- [Focused clean GitHub P3 workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43119195729) passed **36 tests**, an isolated kick+GM-bass A/B with an unchanged drum stem, MP3 decoding, and an integrated After arrangement.
- On the **After** score, 16 anchor notes shifted; median lag was **63.93 → 17.02 ms**. This proves the requested numeric change, not that the new pocket is better.
- The [full recorded-instrument build](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43119410960) **passed** its sample downloads, full baseline renders, P2 integrated renders, and an optional After P3 pocket render. The After P3 metadata confirmed the real sample backend, bass anchor changes and valid decoded MP3.

## Remaining P3 work

Study the *interaction* among snare, hi-hat, kick, bass and percussion accents, including velocity patterns, drum round-robin and micro-timing. Keep all timing adjustments optional until verified on the real sample backend. Subjective approval of "groove feel" remains a listening question; avoid asking for listener input merely to prove events render or compare correctly.

**Status: P3 in progress.** The first pocket experiment is technically valid and ready for further testing; no new finished song is claimed.
