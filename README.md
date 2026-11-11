# Music Studio — original music, made offline

**Default: no third-party generative AI, no API keys, no paid services, no extra user input.** This is a fully reproducible Python digital synthesis studio. ChatGPT can write and edit the arrangement code, then the user's computer or GitHub Actions renders real MP3/WAV/MIDI recordings deterministically. No reference songs, downloaded soundfonts, external samples, or model music outputs are required.

## New complete track: Streetlight Letters

- **3:31**, **116 BPM**, 100 bars, E minor/relative G major.
- **Original composition and melody.** The hooks are composed explicitly; no notes or samples are taken from the user's reference songs.
- **Style:** electronic story-pop meets tight plucked indie-pop, with bass, keys, pads, arpeggios, programmed organic drums, and a singable instrumental lead synth.
- **Form:** opening (8 bars), verse 1 (16), rise (8), chorus 1 (16), instrumental break (8), verse 2 (16), bridge (8), final chorus (16), ending (4).
- **Humanizer:** several deterministic snare/hat timbres, offbeat bass and guitar patterns, responsive counter-melodies, soft saturation, decorrelated stereo delay, low-frequency mono compatibility, and a controlled fade-out.

The repository's GitHub Actions workflow **runs tests before rendering**, then generates the complete MP3, 24-bit WAV, MIDI and score and checks the media. Only passing files are saved as build artifacts and published in a versioned [Streetlight Letters release](https://github.com/goodselldartangan-star/Music_Studio/releases/tag/streetlight-letters-v1). This takes no audio API access.

## Run anywhere with Python

Requirements: Python 3.10+, ffmpeg, and:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python offline_song.py --out output
python audio_quality.py output
```

The final MP3 is `output/Streetlight_Letters.mp3`. `output/Streetlight_Letters.wav` is lossless 24-bit stereo, `output/Streetlight_Letters.mid` contains 9 musical tracks (plus meta track), and `output/Streetlight_Letters.score.json` retains every arranged note and percussion hit.

For score and MIDI without a WAV/MP3 render, use `python offline_song.py --out output --score-only`.

## Reference tracks and privacy

The three user-supplied tracks were assessed **locally only** as broad production references. Two have strong bass, electronic pulse and arpeggios; the guitar-led track has an elastic plucked rhythm and a larger chorus lift. Streetlight Letters translates these broad techniques into a new original instrumental, without copying lyrics, recordings, melodies, or samples. None of the reference recordings are stored in this repository.

## Engineering test coverage

`tests/test_offline_song.py` verifies arrangement, chord coverage, melody repetition, deterministic note/drum lists, sample synthesis and MIDI. `audio_quality.py` verifies all song files, section structure, audio and MP3 decode, exact duration, no clipping, tonal balance, channel balance, mono/stereo correlation, tail fade and dynamic contrast. These tests establish audio integrity and arrangement intent; they do not prove a human will like the sound.

## Existing project files

Earlier original DSP work (`afterglow_atlas.py`) and prior song-planning code (`music_studio.py`) are left intact for reference. The new default build neither calls nor needs the prior OpenAI or ElevenLabs APIs. Previous Afterglow song files were already removed from its GitHub release, but source code was retained as requested.
