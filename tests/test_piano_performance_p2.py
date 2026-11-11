"""P2 piano playing-technique regression tests: no false sustain pedal."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS,validate
from studio7.audit import review
from studio7.piano_performance import shape_piano


class PianoPerformanceTests(unittest.TestCase):
    def test_three_styles_deterministic_and_isolated(self):
        for style in SONGS:
            original=make(style)
            untouched=deepcopy(original)
            after,report=shape_piano(original)
            self.assertEqual(original,untouched)
            self.assertEqual(shape_piano(original),(after,report))
            self.assertEqual(after["drums"],original["drums"])
            self.assertGreater(report["piano_notes"],0)
            self.assertGreater(report["changed_notes"],0)
            self.assertLessEqual(report["max_onset_shift_ms"],24)
            self.assertFalse(report["sustain_pedal"])
            for prev,nxt in zip(original["notes"],after["notes"]):
                self.assertEqual((prev["instrument"],prev["pitch"],prev["length"]),
                                 (nxt["instrument"],nxt["pitch"],nxt["length"]))
                if prev["instrument"]!="piano":
                    self.assertEqual(prev,nxt)
                else:
                    self.assertLessEqual(abs(prev["velocity"]-nxt["velocity"]),9)
                    self.assertLessEqual(abs(prev["beat"]-nxt["beat"])*60/original["bpm"],.024)
            self.assertTrue(validate(after)["validated"])
            self.assertTrue(review(after)["passed"],(style,review(after)))

    def test_existing_piano_roll_becomes_tighter_but_remains_rolled(self):
        score={"bpm":102,"notes":[
            dict(instrument="piano",pitch=62,beat=.08,length=2.,velocity=60),
            dict(instrument="piano",pitch=65,beat=.121,length=2.,velocity=58)],
            "drums":[]}
        shaped,report=shape_piano(score)
        self.assertEqual(report["rolled_chord_groups"],1)
        self.assertEqual(shaped["notes"][0]["beat"],.08)
        delay_s=(shaped["notes"][1]["beat"]-.08)*60/102
        self.assertGreater(delay_s,.010)
        self.assertLess(delay_s,.015)
        self.assertEqual([n["length"] for n in shaped["notes"]],[2.,2.])
        self.assertGreaterEqual(shaped["notes"][0]["velocity"],shaped["notes"][1]["velocity"])

    def test_simultaneous_and_explicit_block_chords_keep_onsets(self):
        score={"bpm":120,"notes":[
            dict(instrument="piano",pitch=p,beat=2.,length=1.,velocity=76)
            for p in (60,64,67)] +
            [dict(instrument="piano",pitch=p,beat=b,length=.9,velocity=70,technique="block")
             for p,b in zip((72,76),(4.,4.04))],
            "drums":[]}
        shaped,report=shape_piano(score)
        self.assertEqual([x["beat"] for x in shaped["notes"]],
                         [x["beat"] for x in score["notes"]])
        self.assertEqual(shaped["notes"][-2:],score["notes"][-2:])

    def test_sustained_note_and_retrigger_not_truncated(self):
        score={"bpm":110,"notes":[
            dict(instrument="piano",pitch=64,beat=.1,length=2.4,velocity=75),
            dict(instrument="piano",pitch=64,beat=1.,length=.3,velocity=62)],"drums":[]}
        after,_=shape_piano(score)
        self.assertEqual([n["beat"] for n in after["notes"]],[.1,1.])
        self.assertEqual([n["length"] for n in after["notes"]],[2.4,.3])

    def test_invalid_piano_range_refused(self):
        score={"bpm":110,"notes":[dict(instrument="piano",pitch=5,beat=.1,length=.4,velocity=75)]}
        with self.assertRaises(ValueError):
            shape_piano(score)


if __name__=="__main__":unittest.main()
