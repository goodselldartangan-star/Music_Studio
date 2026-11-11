# Music Studio — original vocal-song workflow

Music Studio creates **complete original songs with vocals**, not just synthesized instrumental demos. It uses a small, understandable pipeline:

1. **Study a reference locally** for broad stylistic traits (tempo, groove, instrumentation, dynamic shape, vocal delivery) — **never upload or copy the supplied MP3s**.
2. **Write the song with GPT**: original storyline, singable lyrics, recurring chorus, intro/verse/chorus/bridge/outro, and section-level production directions. Store the structured plan as editable JSON.
3. **Generate the performance** with ElevenLabs Music `music_v2_5`, which supports a single full song with lead vocals, band/electronic instrumentation, and planned lyrics.
4. **Test the render** with `ffprobe`/`ffmpeg`: valid stereo audio, plausible duration, audible level, decode success, and near-clipping warnings. Never overwrite an earlier finished master with a failed candidate.
5. **Listen critically yourself** before publication. Technical tests cannot judge vocal emotion, lyric intelligibility, originality, harmony, or mix aesthetics.

The code is intentionally standard-library Python plus `ffmpeg`/`ffprobe` (available on many computers). The test suite runs **offline without any API keys or music charges**. GPT and ElevenLabs are separate paid APIs; ChatGPT subscription access does not automatically fund either API. The ElevenLabs Music API requires a paid account. Never commit keys.

## Reference study (user-supplied examples, not distributed)

| Recording | Duration | Sample-based tempo estimate* | Local MP3 check | Practical direction |
|---|---:|---:|---|---|
| *Don't Let Me Tell It First* | 3:36 | ~112 BPM | Passed | Guitar/bass groove, organic drums, emotionally escalating lead vocal, repeatable chorus |
| *Wrong Kind of Hive* | 4:14 | ~129 BPM | Passed | Atmospheric electronic pop, pulsing analog bass, arpeggiated plucks, intimate-to-melodic lead vocal |
| *Inventory of the Moon* | 4:00 | ~118 BPM | Passed | Third pacing/dynamics reference, suited to the hybrid atmosphere-and-narrative profile |

\*Tempo estimates use beat tracking on 70-second mid-song samples, not formal beat maps; tempo can be heard at half/double rate. Durations and levels were checked with `ffprobe` / `ffmpeg`. The MP3 reference tracks **are not placed in this public repository**, and their lyrics, sound recordings, and melodies are not reused.

## Setup

Requires Python 3.10+ and installed `ffmpeg` and `ffprobe` on your PATH. No pip dependencies for the new pipeline.

```bash
python -m unittest discover -s tests -v
python music_studio.py profiles
python music_studio.py inspect "your-reference.mp3"
python music_studio.py brief --profile electronic_story_pop --concept "A night bus driver finds a handwritten apology"
python music_studio.py validate-plan examples/the_last_ferry_bell.json
python music_studio.py render examples/the_last_ferry_bell.json --dry-run
```

The checked-in `examples/the_last_ferry_bell.json` is **an original demo plan**, not a rendered or published recording. Edit it before spending money on a music render. Profiles: `indie_pop_rock`, `electronic_story_pop`, and `hybrid`.

## GPT planning (explicit paid step)

Choose a concept and optionally an API model supported by your OpenAI API account:

```bash
export OPENAI_API_KEY="..."   # keep this out of git
export OPENAI_MODEL="gpt-6"   # set to a model available on your API account
python music_studio.py plan \
  --profile indie_pop_rock \
  --concept "Two estranged brothers meet at the last ferry of the season" \
  --out output/my_song_plan.json
python music_studio.py validate-plan output/my_song_plan.json
```

The OpenAI Responses API supplies the original composition plan. The local validator catches missing chorus lyrics, out-of-range section lengths, and other malformed requests **before** the expensive render. The GPT planner uses `text.format` JSON mode; inspect and revise the result as needed. You can also write a composition plan by hand without an OpenAI API key.

## Render one vocal song (explicit paid step)

```bash
export ELEVENLABS_API_KEY="..."
python music_studio.py render output/my_song_plan.json --dry-run
python music_studio.py render output/my_song_plan.json --out output/my_song.mp3
python music_studio.py qa output/my_song.mp3
```

The script sends only the composition plan, not the reference MP3 files. It invokes `POST /v1/music` with `model_id=music_v2_5` and `output_format=mp3_48000_192`. Do not add `prompt` or `music_length_ms` alongside `composition_plan` because the provider forbids mixing those input modes. It downloads into `.mp3.partial`, applies QA, then atomically promotes a passing candidate to the final path. The provider may not follow instructions perfectly; listen to the vocal phrasing and review sections manually.

Official documentation: [ElevenLabs composition plans](https://elevenlabs.io/docs/eleven-api/guides/how-to/music/composition-plans) and [music compose API](https://elevenlabs.io/docs/api-reference/music/compose). [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses).

## Tests and retention

`python -m unittest discover -s tests -v` exercises ten independent scenarios, including invalid plans, missing secrets, a mock GPT response, mock streaming, ensuring bad audio doesn't replace a previous master, actual ffmpeg MP3 decoding, and silence rejection. GitHub Actions runs the same offline gates for new code.

The earlier Afterglow Atlas synthesizer code (`afterglow_atlas.py`, `test_audio.py`, `source/`) is **preserved** for future instrumental experiments. The workflow no longer rebuilds or republishes that song. On the first successful push to `main`, the CI cleanup job removes **only** `Afterglow_Atlas.mp3`, `Afterglow_Atlas.wav`, and `Afterglow_Atlas.mid` from the old GitHub release. It preserves the release, the score JSON, all source code, and the historical commit history. Old CI artifacts may remain until their retention period ends.

### Limits of verification

Tests prove the software contracts and MP3 acceptance path, **not** the musical quality of a freshly generated song. A live generation and subjective listening test require funded provider access. Never claim a model-produced track sounds good solely because an audio file passes encoding/level checks.
