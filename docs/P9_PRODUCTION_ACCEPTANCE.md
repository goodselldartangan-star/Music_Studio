# P9 — Production-engineering acceptance and release preservation

**Scope:** archive safety, reproducible test gates and clear boundaries between technical passing status and listener taste. Does not represent a finished professional mix.

## Release asset immutability

The original v7 GitHub Action previously used `gh release upload ... --clobber`, which could replace earlier published MP3s every time a workflow was retriggered. This conflicts with the project's requirement to preserve previously evaluated versions.

`tools/upload_release_if_missing.sh` now reads the release's existing asset names and **uploads only missing files** without ever using `--clobber`. It supports interrupted uploads and is safe to repeat. If two runs race to create the same new asset, the later operation may fail explicitly rather than overwriting it. Historical releases are never deleted or renamed.

[Independent P9 safety workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43153356836) **passed**, including bash syntax and 4 credential-free mock tests: existing asset preservation across two invocations, new-file single-upload idempotence, missing file rejection, and absence of destructive flags in the live workflow.

## Integration and acceptance

- P0 note overlap: independent same-pitch retriggers and chord voicing.
- P1 recorded instrument mapping: actual sample-range/velocity audit.
- P2 instrument gestures: optional guitar, bass and piano touch.
- P3 rhythm connection: optional kick/bass pocket and existing-drum accent shaping.
- P4 register and harmony: optional whole-chord octave spacing while preserving pitch classes.
- P5 melody: phrase/rest audit and one optional closing chord-tone variation.
- P6 room: wet-only predelay, bypass and stereo integrity.
- P7 mix: absolute low-band side power, optional precise mono filtering, true-peak estimate, stem frequency inventory.
- P8 arrangements: optional short backing breath before returning final section.

Each optional change has focused CI and retains original v7 scores, sample banks and unmodified default rendering. Full real-sample workflow runs are referenced in each P0–P8 report.

**Final release-preserving real-library run:** [43153298828](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43153298828) is **pending** at initial report creation; it must pass before claiming P9 integrated acceptance.

## What the tests cannot prove

No total of tests, soundfont velocities, spectral targets or mono-translation numbers establishes artistic appeal or professional-sounding production. In particular, groove feel, harmony warmth, melodic memorability, natural instrumental tone, mix taste, room amount and structural impact need eventual listening-based preference decisions. Keep the settings opt-in until a musical baseline is chosen. For future work, listen only to level-matched 8–16-second variants when a preference genuinely cannot be decided by engineering checks.

**Current completion:** scoped subsystem engineering largely verified; full workflow result pending, artistic acceptance not claimed.
