"""Q4.3 score note timing, authentic SFZ release metadata and opt-in routing."""
import unittest
from unittest.mock import patch
import numpy as np

from studio7.articulation import planned_events,assign_voice_channels,render_polyphonic
from studio7.score import make
from tools.probe_bass_release_q43 import source_release_s,_events


class BassReleaseTests(unittest.TestCase):
    def test_authentic_finger_and_picked_sfz_release_are_not_studio_guard(self):
        self.assertEqual(source_release_s("<group> ampeg_release=0.5"),.5)
        self.assertEqual(source_release_s("<group> ampeg_release=0.3"),.3)
        self.assertRaises(ValueError,source_release_s,"<group> sample=E.flac")
        self.assertRaises(ValueError,source_release_s,"ampeg_release=-0.3")

    def test_180ms_same_pitch_repluck_allocates_channel_differently(self):
        x=planned_events(_events(),120,part="bass")
        self.assertEqual([n["channel"] for n in assign_voice_channels(x,release_guard_s=.12)],
                         [0,0])
        self.assertEqual([n["channel"] for n in assign_voice_channels(x,release_guard_s=.3)],
                         [0,1])
        self.assertEqual([n["channel"] for n in assign_voice_channels(x,release_guard_s=.5)],
                         [0,1])

    def test_different_pitches_can_overlap_without_wasting_a_channel(self):
        src=_events()
        src[1]["pitch"]=38
        x=planned_events(src,120,part="bass")
        self.assertEqual([n["channel"] for n in assign_voice_channels(x,release_guard_s=.5)],
                         [0,0])

    def test_all_original_songs_bass_onsets_and_pitches_unchanged(self):
        for style in ("harbor","after","silver"):
            score=make(style)
            seq=[n for n in score["notes"] if n["instrument"]=="bass"]
            actual=planned_events(seq,score["bpm"],part="bass")
            assert len(actual)==len(seq)
            source=sorted(seq,key=lambda n:(n["beat"],n["pitch"]))
            self.assertEqual([round(e["at"],6) for e in actual],
                             [round(n["beat"]*60/score["bpm"],6) for n in source])
            self.assertEqual([e["pitch"] for e in actual],[n["pitch"] for n in source])

    def test_guard_does_not_mutate_audio_engine_global_release_profile(self):
        from studio7.articulation import PROFILES
        self.assertEqual(PROFILES["bass"].release_s,.12)
        self.assertNotEqual(PROFILES["bass"].release_s,.3)

    def test_non_finite_optional_guard_must_be_rejected_before_soundfont_load(self):
        from pathlib import Path
        for guard in (float("nan"),float("inf"),-1.,4.):
            with self.subTest(guard=guard):
                with self.assertRaises(ValueError):
                    render_polyphonic(Path("/invalid.sf2"),_events(),1.6,120,
                                      part="bass",release_guard_s=guard)


if __name__=="__main__":
    unittest.main()
