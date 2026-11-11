"""P3 kick/bass pocket regression tests (no drum or pickup rewriting)."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS,validate
from studio7.audit import review
from studio7.rhythm import shape_pocket
from tools.audit_rhythm_p3 import inspect_rhythm


class PocketTests(unittest.TestCase):
    def test_all_styles_deterministic_and_no_nonbass_changes(self):
        for style in SONGS:
            before=make(style)
            frozen=deepcopy(before)
            new,report=shape_pocket(before)
            self.assertEqual(before,frozen)
            self.assertEqual(shape_pocket(before),(new,report))
            self.assertEqual(before["drums"],new["drums"])
            self.assertGreater(report["bass_anchors_moved"],0)
            self.assertGreater(report["matched_downbeat_bass"],0)
            for old,nxt in zip(before["notes"],new["notes"]):
                self.assertEqual((old["instrument"],old["pitch"],old["length"],old["velocity"]),
                                 (nxt["instrument"],nxt["pitch"],nxt["length"],nxt["velocity"]))
                if old["instrument"]!="bass" or old["beat"]%4>=.38:
                    self.assertEqual(old,nxt)
                if old["instrument"]=="bass":
                    self.assertLessEqual(old["beat"]-nxt["beat"],.121)
            self.assertTrue(validate(new)["validated"])
            self.assertTrue(review(new)["passed"],(style,review(new)))
            after=inspect_rhythm(new)
            before_report=inspect_rhythm(before)
            self.assertEqual(after["bass_notes"],before_report["bass_notes"])
            self.assertLess(after["bass_anchor_offset_ms_median"],
                            before_report["bass_anchor_offset_ms_median"])

    def test_calm_intro_without_kick_unchanged(self):
        old=make("silver")
        new,_=shape_pocket(old)
        for prev,nxt in zip(old["notes"],new["notes"]):
            if prev["instrument"]=="bass" and 16<=prev["beat"]<32:
                self.assertEqual(prev,nxt)

    def test_previous_note_release_blocks_timing_change(self):
        score={"style":"harbor","bpm":120,"notes":[
            dict(instrument="bass",pitch=36,beat=3.80,length=.25,velocity=80),
            dict(instrument="bass",pitch=36,beat=4.12,length=.8,velocity=90)],
            "drums":[dict(kind="kick",beat=4,velocity=89)]}
        result,report=shape_pocket(score)
        self.assertEqual(result["notes"][1]["beat"],4.12)
        self.assertEqual(report["skipped_to_preserve_rest_or_overlap"],1)

    def test_unrelated_pickup_stays_behind_grid(self):
        score={"style":"after","bpm":120,"notes":[
            dict(instrument="bass",pitch=40,beat=.13,length=.6,velocity=80),
            dict(instrument="bass",pitch=40,beat=1.65,length=.3,velocity=65)],
            "drums":[dict(kind="kick",beat=0,velocity=90),
                     dict(kind="kick",beat=1.77,velocity=72)]}
        changed,report=shape_pocket(score)
        self.assertLess(changed["notes"][0]["beat"],.13)
        self.assertEqual(changed["notes"][1],score["notes"][1])
        self.assertEqual(report["unmodified_pickups"],1)

    def test_invalid_target_rejected(self):
        score=make("harbor")
        for target in (-1,120,float("nan")):
            with self.assertRaises(ValueError):
                shape_pocket(score,target_lag_ms=target)


if __name__=="__main__":unittest.main()
