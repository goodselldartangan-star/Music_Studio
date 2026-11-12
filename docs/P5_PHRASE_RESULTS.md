# P5 — Melody phrasing and authored closing cadence

**Engineering scope:** inspect the existing 16-bar sketch motifs and create one optional final-phrase alternative. This does **not** evaluate catchiness or guarantee emotional impact.

## Symbolic phrase audit

`tools.audit_phrases_p5` reports note totals, explicit rests, long held notes, and recurring motif structure for each of three sections (beats 16–32, 32–48, 48–64). Counts from the clean GitHub runner:

| Style | Lead notes per section | Positive rests per section | Notes lasting >=1 beat per section |
|---|---|---|---|
| Harbor | 9 / 11 / 11 | 8 / 10 / 10 | 2 / 3 / 3 |
| After | 9 / 10 / 10 | 8 / 9 / 9 | 2 / 2 / 2 |
| Silver | 8 / 8 / 8 | 7 / 7 / 7 | 5 / 5 / 5 |

These counts establish that rests and longer notes exist, **not** that the melodies are original, moving, or memorable. More notes is not the goal.

## Controlled optional variation

`studio7/melody.py::shape_final_answer` changes **exactly one closing foreground note** for each style. Each alternative is a chord tone of the final bar (Harbor G, After A, Silver E). Opening/verse/build hook identity, other notes, drum hits, instrument patches, and mix remain unchanged.

The optional CLI flag is `--melody-answer`. The default output is untouched, with separate `-p5-answer` filenames for comparison.

## Verified technical checks

- [P5 clean runner 43149596445](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43149596445) passed **31 unit tests**, the score-only phrase report, identical-patch melody A/B render and a complete optional After MP3 render.
- Existing [P5 run 43125967486](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43125967486) passed earlier 27 tests and a matched melody comparison.
- Full recorded-instrument verification: [workflow 43149618708](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43149618708). **Passed**: the real instrument libraries were downloaded, the optional After P5 cadence rendered with its original sampled lead and accompaniment, and the MP3 QA gate succeeded.

## Acceptance caveat

P5's mechanical/symbolic correctness can pass automated tests, but **memorability, emotional phrasing and the best ending are subjective**. The alternate ending remains opt-in. Do not claim it is artistically better without listener evaluation; do not force user to listen merely to establish that a MIDI note lands inside a chord.
