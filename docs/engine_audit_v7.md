# Music Studio v7: instrument compatibility, playing technique, and effects audit

**Scope:** Build three short original audio comparisons, not another full song. GPT is the only generative AI; the renderer uses ordinary offline DSP, recording samples and a SoundFont player. Existing v6 material is preserved. We do not claim that numerical tests make music aesthetically good.

## Diagnoses verified against v6

| Component | v6 issue | v7 change | What can be tested |
|---|---|---|---|
| Bass notes | v6 examples sometimes add an entire octave to roots, above the FreePats FingerBassYR source range (native sampled up to MIDI 45), requiring transposition of its highest source notes. | Restrict both finger and picked bass to MIDI 26–45; separate bass onset from kick by 0.11–0.16 beat. | Native range test, note/beat event inspection |
| Guitar voicing | v6 electric rhythm puts one chord tone an octave above the other two (one chord spans ~17 semitones). | Use playable three-note close chord voicings with distinct rhythms and staggered string attacks. | Verify chord-note span and lead/harmony register |
| Harmonic clashes | v6 used key-membership but didn't check semitone overlaps between concurrent piano and melodic notes. | Separate collision audit, plus deliberate chord-tone resolution where accompaniment holds a major third. | Note-time overlap test |
| Instrument roles | Similar lead, arpeggio and chord rhythms can mask one another. | Acoustic guitar rhythm and electric fills (A); rhythm electric, piano offbeats and electric topline (B); piano chords and delayed guitar answers (C). | Per-role onset counts, score identity |
| Drum/bass coupling | v6 simply superimposes dry stems. | Tempo-aligned bass and kick, a conservative sidechain envelope on bass only, centered low end. | Sidechain test, low-frequency balance |
| Space and effects | v6 mostly high-passes, mixes and fades, with isolated SF2 patches. | Shared filtered room send; specific guitar tempo delay, rhythmic tremolo and mild stereo chorus, selective saturation, high-pass and low-pass by role. | Wet-vs-dry DSP differences and test MP3 decode |
| Instrument variety | v6 had finger electric bass and steel guitar. | Optional FreePats picked bass for B and Meta CC0 nylon guitar for C. | Publisher archive and installed sample provenance; pitch range fixtures |

## General research: what tends to help

- **Arrangement before EQ.** Instruments can compete in the same register and time. Use octave, space, note duration, alternating phrases and rhythmic placement to reserve focus for the lead. Frequency masking is not always a defect, but unintentional overlap often is. [Sound on Sound: achieving separation](https://www.soundonsound.com/techniques/how-achieve-better-separation-your-mixes); [iZotope: masking](https://www.izotope.com/en/learn/what-is-frequency-masking).
- **Realistic sample playback.** Don't treat every instrument as a generic pitched sine. Recorded attacks, velocity layers, and distinct playing techniques make the same score feel different. Our v7 source uses external CC0 guitar/piano and FreePats bass/guitar libraries with conventional SF2/SFZ decoding.
- **Production effects have musical jobs.** A guitar delay can fill space *between* lead notes, not merely make all notes ring longer. Shared reverb places parts in a consistent acoustic space; its wet signal is filtered to avoid muddy bass. Finneas has shown deliberate sound choices tied to the song, including found-object percussion and changing bandwidth at section entrances. [Pitchfork production interview](https://pitchfork.com/video/watch/finneas-critical-breakthroughs); [NPR on context of arrangement](https://www.wcmu.org/music/2024-05-17/billie-eilish-finally-remembers-who-she-is).
- **Dry and processed parallel guitar is useful.** Coldplay producer Ken Nelson described retaining dry guitar as an alternative alongside delay processing, rather than always committing to one wet guitar sound. Our new music examples use modest dry/wet sends, not a commercial preset imitation. [Interview](https://coldplaying.com/newsarchive/articles/countdown-to-10th-anniversary-of-parachutes-ken-nelson-on-recording-coldplays-debut-album/).
- **Low-frequency hierarchy.** Reserve the sub and kick transient for the rhythm section, high-pass guitar and piano as warranted, keep bass mono-compatible, use conservative sidechain only where there is a collision. Avoid indiscriminate global mastering because it can flatten the groove. [Sound on Sound: mixing essentials](https://www.soundonsound.com/techniques/mixing-essentials).

## Three controlled v7 listening sketches

- **The Harbor Light** (D major / 108 BPM, 38.6 s): steel-string acoustic rhythm; small piano accents; electric lead guitar responses; finger bass; natural drums. Shared short room, tiny guitar delay, no global chorus.
- **After the Signal** (E minor / 122 BPM, 34.5 s): tight electric chord stabs and higher melody, picked bass, piano offbeats; punchy real acoustic drums; tempo-sync 3/4-beat guitar delay, tremolo, slight chorus. Deliberately restrained reverb.
- **Silver Rain** (D minor / 102 BPM, 40.7 s): piano led, quieter guitar answers, nylon-string guitar late texture, finger bass, half-time drum entrance; longer room send, 1-beat guitar delay and gentle modulation.

Scores are original and do not reproduce the reference recordings' melodies, lyrics or audio. The names of popular artists are research inspiration for general production techniques, not target identities or styles to imitate exactly.

## Testing gate

1. Validate key, note ranges, a playable guitar chord span, note overlap and pitch without generating audio.
2. Test all independent FX with synthetic fixtures to ensure they actually alter audio, remain finite, and preserve sample counts.
3. Render local General MIDI fallback, decode all MP3s, check peaks, silence, bass, stereo and duration. **This is not the real sampled-instrument final**; the fallback enables offline regression tests.
4. On GitHub Actions, download publisher-sourced Meta, FreePats and MuldjordKit samples, verify SHA-256 provenance, render the same three arrangements and test decoded outputs. CC BY 4.0 attribution: MuldjordKit drum samples by DrumGizmo.org. Meta and FreePats packs used here are CC0.
5. Publish the recorded-instrument MP3s as *listening demos*, not as professionally approved songs. Accept or reject them through user feedback before promoting an arrangement to a full single.

**Limitations:** This engine cannot literally hear like a human sound engineer. Note-harmony tests cannot identify every intentional tension. Signal measurements provide engineering guardrails, not a preference score. No other AI music model is involved.
