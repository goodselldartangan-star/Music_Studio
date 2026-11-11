"""P3 baseline audit: deterministic read-only timing measurements."""
import unittest
from copy import deepcopy
from studio7.score import make, SONGS
from tools.audit_rhythm_p3 import inspect_rhythm


class RhythmAudit(unittest.TestCase):
    def test_all_three_styles_have_unmodified_scores_and_measurable_groove(self):
        for style in SONGS:
            song=make(style)
            frozen=deepcopy(song)
            report=inspect_rhythm(song)
            self.assertEqual(song,frozen)
            self.assertEqual(report,inspect_rhythm(song))
            self.assertGreater(report["bass_notes"],0)
            self.assertGreater(report["kick_hits"],0)
            self.assertEqual(report["bass_notes"],
                             report["other_bass_notes"]+report["downbeat_bass_kick_pairs"]+
                             len(report["unpaired_downbeat_bass"]))
            self.assertEqual(len(report["anchor_offsets_ms"]),report["downbeat_bass_kick_pairs"])
    def test_offset_sign_and_pickup_not_forced_to_kick(self):
        score={"style":"test","bpm":120,
               "notes":[dict(instrument="bass",beat=.12,length=.8,pitch=40,velocity=80),
                        dict(instrument="bass",beat=3.50,length=.3,pitch=40,velocity=62)],
               "drums":[dict(kind="kick",beat=0,velocity=90),
                        dict(kind="snare",beat=1.02,velocity=75),
                        dict(kind="hat",beat=.51,velocity=42)]}
        result=inspect_rhythm(score)
        self.assertEqual(result["downbeat_bass_kick_pairs"],1)
        self.assertEqual(result["bass_anchor_offset_ms_median"],60.)
        self.assertEqual(result["other_bass_notes"],1)
        self.assertEqual(result["snare_grid_offset_ms_median"],10.)
        self.assertEqual(result["hat_halfbeat_offset_ms_median"],5.)
    def test_no_drums_does_not_crash_or_relabel_bass(self):
        score={"style":"intro","bpm":105,"notes":[dict(instrument="bass",beat=.1,pitch=38,length=1,velocity=70)],"drums":[]}
        r=inspect_rhythm(score)
        self.assertEqual(r["downbeat_bass_kick_pairs"],0)
        self.assertEqual(r["unpaired_downbeat_bass"],[.1])
        self.assertIsNone(r["bass_anchor_offset_ms_median"])


if __name__=="__main__":unittest.main()
