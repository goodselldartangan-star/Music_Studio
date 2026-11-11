"""P2 bass articulation contract tests."""
import unittest
from copy import deepcopy
from studio7.score import make, SONGS, validate
from studio7.audit import review
from studio7.bass_performance import shape_bass


class BassPerformanceTests(unittest.TestCase):
    def test_three_styles_keep_score_and_other_instruments_unchanged(self):
        for style in SONGS:
            original=make(style)
            unchanged=deepcopy(original)
            result,info=shape_bass(original)
            self.assertEqual(original,unchanged)
            self.assertEqual(shape_bass(original),(result,info))
            self.assertEqual(result["drums"],original["drums"])
            self.assertGreater(info["bass_notes"],0)
            self.assertGreater(info["changed_notes"],0)
            self.assertLessEqual(info["max_duration_change_beats"],.071)
            for old,new in zip(original["notes"],result["notes"]):
                if old["instrument"]!="bass":
                    self.assertEqual(old,new)
                else:
                    self.assertEqual((old["beat"],old["pitch"]), (new["beat"],new["pitch"]))
                    self.assertLessEqual(abs(old["velocity"]-new["velocity"]),5)
                    self.assertLessEqual(abs(old["length"]-new["length"]),.071)
                    self.assertGreater(new["length"],0)
            self.assertTrue(validate(result)["validated"])
            self.assertTrue(review(result)["passed"],(style,review(result)))

    def test_pickup_is_quieter_and_shorter_but_not_silent(self):
        score={"bpm":116,"notes":[
            dict(instrument="bass",pitch=36,beat=3.53,length=.35,velocity=75),
            dict(instrument="bass",pitch=36,beat=4.12,length=.98,velocity=79),
            dict(instrument="bass",pitch=36,beat=6.1,length=.56,velocity=70)]}
        result,report=shape_bass(score)
        self.assertEqual(result["notes"][0]["velocity"],71)
        self.assertLess(result["notes"][0]["length"],.35)
        self.assertGreater(result["notes"][0]["length"],.28)
        self.assertEqual(result["notes"][1]["velocity"],84)
        self.assertGreater(result["notes"][1]["length"],.98)
        self.assertLess(result["notes"][1]["beat"]+result["notes"][1]["length"],6.1)

    def test_preserve_overlapping_long_and_short_same_pitch_notes(self):
        score={"bpm":110,"notes":[
            dict(instrument="bass",pitch=38,beat=.15,length=2.1,velocity=85),
            dict(instrument="bass",pitch=38,beat=1.2,length=.25,velocity=62)]}
        result,report=shape_bass(score)
        self.assertEqual(result["notes"][0]["length"],2.1)
        self.assertEqual(report["preserved_overlaps"],1)
        self.assertEqual(result["notes"][1]["beat"],1.2)
        self.assertEqual(result["notes"][1]["pitch"],38)

    def test_explicit_hold_and_nonbass_parts_untouched(self):
        note=dict(instrument="bass",pitch=40,beat=0.,length=1.,velocity=75,technique="hold")
        score={"bpm":120,"notes":[note,dict(instrument="piano",pitch=64,beat=0.,length=2.,velocity=77)]}
        result,report=shape_bass(score)
        self.assertEqual(result,score)
        self.assertEqual(report["changed_notes"],0)

    def test_bad_bass_event_rejected(self):
        for pitch in (11,48):
            score={"bpm":120,"notes":[dict(instrument="bass",pitch=pitch,beat=0.,length=.5,velocity=80)]}
            with self.assertRaises(ValueError):
                shape_bass(score)


if __name__=="__main__":unittest.main()
